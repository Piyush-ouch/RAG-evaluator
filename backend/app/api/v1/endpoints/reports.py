"""Reports API Endpoints."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.report import Report

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/")
async def list_reports(
    db: DbSession,
    current_user: CurrentUser,
    evaluation_id: uuid.UUID | None = None,
) -> list[dict]:
    """List generated reports."""
    stmt = select(Report).where(Report.org_id == current_user.org_id)
    if evaluation_id:
        stmt = stmt.where(Report.evaluation_id == evaluation_id)
    stmt = stmt.order_by(Report.created_at.desc())
    result = await db.execute(stmt)
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "evaluation_id": str(r.evaluation_id),
            "report_type": r.report_type,
            "format": r.format,
            "title": r.title,
            "file_size_bytes": r.file_size_bytes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.post("/{evaluation_id}/generate")
async def generate_report(
    evaluation_id: uuid.UUID,
    report_type: str = "full",
    format: str = "pdf",
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Trigger report generation for an evaluation."""
    from app.workers.tasks.report_tasks import generate_report_task
    task = generate_report_task.delay(
        evaluation_id=str(evaluation_id),
        report_type=report_type,
        format=format,
        org_id=str(current_user.org_id),
    )
    return {"message": "Report generation started.", "task_id": task.id}


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get a presigned URL to download a report."""
    stmt = select(Report).where(
        Report.id == report_id,
        Report.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError("Report", str(report_id))

    from app.core.storage import storage_client
    url = await storage_client.generate_presigned_url(report.file_path)
    return {"download_url": url}
