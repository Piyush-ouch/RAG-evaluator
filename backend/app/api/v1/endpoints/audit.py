"""Audit Log Endpoints."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Pagination
from app.models.audit_log import AuditLog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
async def list_audit_logs(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
    action: str | None = None,
    resource_type: str | None = None,
) -> list[dict]:
    """List audit logs for the organization."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.org_id == current_user.org_id)
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    stmt = (
        stmt.order_by(AuditLog.timestamp.desc())
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
    )
    result = await db.execute(stmt)
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in result.scalars().all()
    ]
