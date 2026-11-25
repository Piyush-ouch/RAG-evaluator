"""
Evaluation Repository

Domain repository handling evaluation run persistence and aggregate query execution.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.models.evaluation import Evaluation, EvaluationResult


class EvaluationRepository(BaseRepository[Evaluation]):
    """Repository for Evaluation entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Evaluation, session)

    async def find_by_project(
        self,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
        limit: int = 50,
    ) -> Sequence[Evaluation]:
        """Fetch evaluation runs for a specific project."""
        return await self.find_many(
            Evaluation.project_id == project_id,
            org_id=org_id,
            order_by=Evaluation.created_at.desc(),
            limit=limit,
        )

    async def get_latest_completed_run(
        self,
        project_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> Evaluation | None:
        """Fetch the most recent completed evaluation run for regression baseline comparison."""
        return await self.find_one(
            Evaluation.project_id == project_id,
            Evaluation.status == "completed",
            org_id=org_id,
        )
