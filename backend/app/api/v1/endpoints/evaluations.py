"""
Evaluation API Endpoints
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.core.constants import EvaluationStatus, UserRole
from app.core.exceptions import NotFoundError, ValidationError
from app.models.benchmark import BenchmarkSuite
from app.models.evaluation import Evaluation, EvaluationResult
from app.models.project import Project
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationResultResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.get("/", response_model=list[EvaluationResponse])
async def list_evaluations(
    db: DbSession,
    current_user: CurrentUser,
    project_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[EvaluationResponse]:
    """List evaluations, optionally filtered by project and status."""
    stmt = select(Evaluation).where(Evaluation.org_id == current_user.org_id)
    if project_id:
        stmt = stmt.where(Evaluation.project_id == project_id)
    if status:
        stmt = stmt.where(Evaluation.status == status)
    stmt = stmt.order_by(Evaluation.created_at.desc())
    result = await db.execute(stmt)
    return [EvaluationResponse.model_validate(e, from_attributes=True)
            for e in result.scalars().all()]


@router.post(
    "/",
    response_model=EvaluationResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
)
async def create_evaluation(
    request: EvaluationCreate,
    project_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> EvaluationResponse:
    """
    Create and start a new evaluation.

    This creates the evaluation record and dispatches the benchmark
    execution to Celery workers.
    """
    # Validate project
    stmt = select(Project).where(
        Project.id == project_id,
        Project.org_id == current_user.org_id,
        Project.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))

    if not project.chatbot_api_url:
        raise ValidationError("Project has no chatbot API configured.")

    # Validate suite
    suite_stmt = select(BenchmarkSuite).where(BenchmarkSuite.id == request.suite_id)
    suite_result = await db.execute(suite_stmt)
    suite = suite_result.scalar_one_or_none()
    if not suite:
        raise NotFoundError("BenchmarkSuite", str(request.suite_id))

    evaluation = Evaluation(
        project_id=project_id,
        suite_id=request.suite_id,
        org_id=current_user.org_id,
        name=request.name,
        description=request.description,
        version_tag=request.version_tag,
        status=EvaluationStatus.PENDING.value,
        total_questions=suite.question_count,
        enabled_evaluators=request.enabled_evaluators,
        triggered_by_id=current_user.id,
        config_snapshot={
            "chatbot_url": project.chatbot_api_url,
            "chatbot_method": project.chatbot_api_method,
        },
    )
    db.add(evaluation)
    await db.flush()
    await db.refresh(evaluation)

    # Dispatch to Celery
    from app.workers.tasks.evaluation_tasks import run_benchmark
    task = run_benchmark.delay(str(evaluation.id))
    evaluation.celery_task_id = task.id

    logger.info("evaluation_started", eval_id=str(evaluation.id), task_id=task.id)

    return EvaluationResponse.model_validate(evaluation, from_attributes=True)


@router.get("/{eval_id}", response_model=EvaluationResponse)
async def get_evaluation(
    eval_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> EvaluationResponse:
    """Get evaluation details with progress."""
    stmt = select(Evaluation).where(
        Evaluation.id == eval_id,
        Evaluation.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise NotFoundError("Evaluation", str(eval_id))
    return EvaluationResponse.model_validate(evaluation, from_attributes=True)


@router.get("/{eval_id}/results", response_model=list[EvaluationResultResponse])
async def get_evaluation_results(
    eval_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
) -> list[EvaluationResultResponse]:
    """Get paginated evaluation results."""
    stmt = (
        select(EvaluationResult)
        .where(EvaluationResult.evaluation_id == eval_id)
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
    )
    result = await db.execute(stmt)
    return [EvaluationResultResponse.model_validate(r, from_attributes=True)
            for r in result.scalars().all()]


@router.post("/{eval_id}/cancel")
async def cancel_evaluation(
    eval_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Cancel a running evaluation."""
    stmt = select(Evaluation).where(
        Evaluation.id == eval_id,
        Evaluation.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise NotFoundError("Evaluation", str(eval_id))

    if evaluation.status not in (EvaluationStatus.PENDING.value, EvaluationStatus.RUNNING.value):
        raise ValidationError("Can only cancel pending or running evaluations.")

    evaluation.status = EvaluationStatus.CANCELLED.value
    evaluation.completed_at = datetime.now(timezone.utc)

    # Revoke Celery task
    if evaluation.celery_task_id:
        from app.workers.celery_app import celery_app
        celery_app.control.revoke(evaluation.celery_task_id, terminate=True)

    return {"message": "Evaluation cancelled."}
