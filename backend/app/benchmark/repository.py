"""
Benchmark Repository Layer

Encapsulates database persistence and query operations for BenchmarkSuite and Question models.
Interacts with PostgreSQL using async SQLAlchemy sessions.
"""

from __future__ import annotations

import uuid
from typing import Sequence

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.benchmark.deduplicator import QuestionDeduplicator
from app.benchmark.normalizer import CanonicalQuestion
from app.models.benchmark import BenchmarkSuite, Question
from app.models.organization import Organization
from app.models.project import Project

logger = structlog.get_logger(__name__)


class BenchmarkRepository:
    """Repository handling database operations for benchmark suites and questions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_default_project(
        self, org_id: uuid.UUID | None = None
    ) -> Project:
        """Resolve or create an active project to associate with standard benchmark suites."""
        if not org_id:
            org_stmt = select(Organization).limit(1)
            org_res = await self.session.execute(org_stmt)
            org = org_res.scalar_one_or_none()
            if not org:
                org = Organization(name="Default Organization", slug="default-org")
                self.session.add(org)
                await self.session.flush()
            org_id = org.id

        p_stmt = select(Project).where(Project.org_id == org_id).limit(1)
        p_res = await self.session.execute(p_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            project = Project(
                org_id=org_id,
                name="Benchmark Project",
                slug="benchmark-project",
                description="Project hosting canonical domain benchmark suites.",
                chatbot_api_url="http://localhost:8000/api/v1/demo/chatbot",
            )
            self.session.add(project)
            await self.session.flush()

        return project

    async def get_or_create_ragbench_suite(
        self,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
        name: str,
        domain: str,
        description: str,
        subset: str,
        version: str = "1.0",
    ) -> BenchmarkSuite:
        """Find existing RAGBench suite by source provenance, or create a new one."""
        stmt = select(BenchmarkSuite).where(
            BenchmarkSuite.source_dataset == "ragbench",
            BenchmarkSuite.source_subset == subset.lower(),
        )
        res = await self.session.execute(stmt)
        suite = res.scalar_one_or_none()

        if not suite:
            # Fallback by exact name matching
            stmt_name = select(BenchmarkSuite).where(BenchmarkSuite.name == name)
            res_name = await self.session.execute(stmt_name)
            suite = res_name.scalar_one_or_none()

        if not suite:
            suite = BenchmarkSuite(
                project_id=project_id,
                org_id=org_id,
                name=name,
                domain=domain,
                description=description,
                version=version,
                is_template=True,
                source_dataset="ragbench",
                source_subset=subset.lower(),
                metadata_json={
                    "source": "rungalileo/ragbench",
                    "subset": subset.lower(),
                    "benchmark_type": "rag",
                },
            )
            self.session.add(suite)
            await self.session.flush()
            await self.session.refresh(suite)
        else:
            # Ensure provenance fields are populated
            suite.source_dataset = "ragbench"
            suite.source_subset = subset.lower()
            if not suite.version:
                suite.version = version

        return suite

    async def get_existing_question_identity_keys(self, suite_id: uuid.UUID) -> set[str]:
        """Fetch canonical identity keys for all questions in the suite to avoid duplicates."""
        stmt = select(
            Question.source_dataset,
            Question.source_subset,
            Question.source_question_id,
            Question.dataset_version,
            Question.text,
        ).where(Question.suite_id == suite_id)

        res = await self.session.execute(stmt)
        keys = set()
        for row in res.all():
            s_dataset, s_subset, s_id, s_ver, q_text = row
            if s_dataset and s_subset and s_id:
                keys.add(
                    QuestionDeduplicator.get_identity_key(
                        source_dataset=s_dataset,
                        source_subset=s_subset,
                        source_question_id=s_id,
                        dataset_version=s_ver or "1.0",
                    )
                )
            elif q_text:
                # Fallback on text hash for legacy questions
                keys.add(q_text.strip().lower())
        return keys

    async def insert_question(
        self,
        suite_id: uuid.UUID,
        q: CanonicalQuestion,
        order_index: int,
    ) -> Question:
        """Insert a single normalized CanonicalQuestion into PostgreSQL."""
        question = Question(
            suite_id=suite_id,
            text=q.question,
            expected_answer=q.expected_answer,
            expected_context=q.expected_context,
            category=q.category,
            subcategory=q.subcategory,
            difficulty=q.difficulty,
            evaluation_type=q.evaluation_type,
            order_index=order_index,
            source_dataset=q.source_dataset,
            source_subset=q.source_subset,
            source_question_id=q.source_question_id,
            dataset_version=q.dataset_version,
            is_active=q.is_active,
            tags=q.tags,
            metadata_json=q.metadata_json,
        )
        self.session.add(question)
        return question

    async def update_suite_question_count(self, suite_id: uuid.UUID) -> int:
        """Recalculate and update the question_count column for a suite."""
        count_stmt = select(func.count(Question.id)).where(Question.suite_id == suite_id)
        count_res = await self.session.execute(count_stmt)
        actual_count = count_res.scalar_one() or 0

        suite_stmt = select(BenchmarkSuite).where(BenchmarkSuite.id == suite_id)
        suite_res = await self.session.execute(suite_stmt)
        suite = suite_res.scalar_one_or_none()
        if suite:
            suite.question_count = actual_count
            await self.session.flush()

        return actual_count
