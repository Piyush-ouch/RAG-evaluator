"""
Evaluation Service Layer

Dedicated Evaluation Service governing evaluation run creation, asynchronous job dispatching,
progress tracking, PostgreSQL persistence, and metrics aggregation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EvaluationStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.benchmark import BenchmarkSuite
from app.models.evaluation import Evaluation, EvaluationResult
from app.models.project import Project

logger = structlog.get_logger(__name__)


class EvaluationService:
    """Service layer for Orchestrating RAG Evaluations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_evaluation_run(
        self,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        suite_id: uuid.UUID,
        name: str,
        enabled_evaluators: list[str] | None = None,
        triggered_by_id: uuid.UUID | None = None,
        version_tag: str | None = None,
    ) -> Evaluation:
        """Create and queue an evaluation run in PostgreSQL and Celery."""
        # Verify project
        p_stmt = select(Project).where(Project.id == project_id, Project.org_id == org_id)
        p_result = await self.db.execute(p_stmt)
        project = p_result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))

        if not project.chatbot_api_url:
            raise ValidationError("Project has no configured Chatbot API URL.")

        # Verify suite
        s_stmt = select(BenchmarkSuite).where(BenchmarkSuite.id == suite_id)
        s_result = await self.db.execute(s_stmt)
        suite = s_result.scalar_one_or_none()
        if not suite:
            raise NotFoundError("BenchmarkSuite", str(suite_id))

        default_evaluators = [
            "correctness", "faithfulness", "hallucination",
            "prompt_injection", "jailbreak", "pii_leakage",
            "latency", "cost",
        ]

        evaluation = Evaluation(
            org_id=org_id,
            project_id=project_id,
            suite_id=suite_id,
            name=name,
            version_tag=version_tag,
            status=EvaluationStatus.PENDING.value,
            total_questions=suite.question_count,
            enabled_evaluators=enabled_evaluators or default_evaluators,
            triggered_by_id=triggered_by_id,
            config_snapshot={
                "chatbot_url": project.chatbot_api_url,
                "chatbot_method": project.chatbot_api_method,
                "llm_provider": (project.settings or {}).get("llm_provider", "openai"),
                "vector_db": (project.settings or {}).get("vector_db", "chroma"),
            },

        )
        self.db.add(evaluation)
        await self.db.flush()
        await self.db.refresh(evaluation)

        # Dispatch Celery background task without blocking async loop
        import asyncio
        from app.workers.celery_app import celery_app
        run_in_process_fallback = False
        try:
            task = await asyncio.to_thread(
                celery_app.send_task,
                "app.workers.tasks.evaluation_tasks.run_benchmark",
                args=[str(evaluation.id)],
            )
            evaluation.celery_task_id = task.id
        except Exception as err:
            logger.warning("celery_dispatch_failed_fallback_local", error=str(err))
            evaluation.celery_task_id = str(uuid.uuid4())
            run_in_process_fallback = True

        await self.db.commit()
        if run_in_process_fallback:
            from app.workers.tasks.evaluation_tasks import _run_benchmark_async
            asyncio.create_task(_run_benchmark_async(str(evaluation.id)))
        logger.info("evaluation_run_dispatched", eval_id=str(evaluation.id))
        return evaluation


    async def get_evaluation(self, eval_id: uuid.UUID, org_id: uuid.UUID | None = None) -> Evaluation:
        """Get evaluation record by ID."""
        stmt = select(Evaluation).where(Evaluation.id == eval_id)
        if org_id:
            stmt = stmt.where(Evaluation.org_id == org_id)
        result = await self.db.execute(stmt)
        evaluation = result.scalar_one_or_none()
        if not evaluation:
            raise NotFoundError("Evaluation", str(eval_id))
        return evaluation

    async def list_evaluations(
        self, org_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> list[Evaluation]:
        """List evaluation runs for an organization."""
        stmt = select(Evaluation).where(Evaluation.org_id == org_id)
        if project_id:
            stmt = stmt.where(Evaluation.project_id == project_id)
        stmt = stmt.order_by(Evaluation.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_results(
        self, eval_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> list[EvaluationResult]:
        """Get paginated per-question evaluation results."""
        stmt = (
            select(EvaluationResult)
            .where(EvaluationResult.evaluation_id == eval_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def cancel_evaluation(self, eval_id: uuid.UUID, org_id: uuid.UUID) -> Evaluation:
        """Cancel a pending or running evaluation."""
        evaluation = await self.get_evaluation(eval_id, org_id)
        if evaluation.status not in [EvaluationStatus.PENDING.value, EvaluationStatus.RUNNING.value]:
            raise ValidationError("Can only cancel pending or running evaluations.")

        evaluation.status = EvaluationStatus.CANCELLED.value
        evaluation.completed_at = datetime.now(timezone.utc)

        if evaluation.celery_task_id:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(str(evaluation.celery_task_id), terminate=True)

        await self.db.commit()
        return evaluation
