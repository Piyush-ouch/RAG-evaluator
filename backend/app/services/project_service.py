"""
Project Service Layer

Handles operations for managing project configurations and testing HTTP connections.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.project import Project

logger = structlog.get_logger(__name__)


class ProjectService:
    """Service layer for Project management and connectivity testing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(self, org_id: uuid.UUID) -> list[Project]:
        """List all non-deleted projects for an organization."""
        stmt = (
            select(Project)
            .where(Project.org_id == org_id, Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_project(self, project_id: uuid.UUID, org_id: uuid.UUID) -> Project:
        """Get a specific project by ID and org_id."""
        stmt = select(Project).where(
            Project.id == project_id,
            Project.org_id == org_id,
            Project.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))
        return project

    async def create_project(
        self,
        org_id: uuid.UUID,
        name: str,
        description: str | None = None,
        chatbot_api_url: str | None = None,
        chatbot_api_method: str = "POST",
        llm_provider: str = "openai",
        vector_db: str = "chroma",
    ) -> Project:
        """Create a new project."""
        from slugify import slugify
        project = Project(
            org_id=org_id,
            name=name,
            slug=slugify(name),
            description=description,
            chatbot_api_url=chatbot_api_url,
            chatbot_api_method=chatbot_api_method,
            settings={
                "llm_provider": llm_provider,
                "vector_db": vector_db,
            },
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project


    async def delete_project(self, project_id: uuid.UUID, org_id: uuid.UUID) -> None:
        """Soft delete a project."""
        project = await self.get_project(project_id, org_id)
        from datetime import datetime, timezone
        project.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    @staticmethod
    async def test_connection(
        url: str, method: str = "POST", headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Test connection to customer's Chatbot API endpoint.
        """
        start = time.perf_counter()
        headers = headers or {"Content-Type": "application/json"}
        test_payload = {"query": "Ping connectivity health check"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.request(
                    method=method, url=url, json=test_payload, headers=headers
                )
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                return {
                    "online": resp.is_success,
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms,
                    "message": f"Endpoint responded with HTTP status {resp.status_code}",
                }
        except Exception as err:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.warning("project_connection_test_failed", url=url, error=str(err))
            return {
                "online": False,
                "status_code": 0,
                "latency_ms": latency_ms,
                "message": f"Connection failed: {str(err)}",
            }
