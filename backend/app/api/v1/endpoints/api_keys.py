"""API Key Management Endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.core.security import generate_api_key
from app.models.api_key import ApiKey

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.get("/")
async def list_api_keys(db: DbSession, current_user: CurrentUser) -> list[dict]:
    """List API keys for the organization."""
    stmt = select(ApiKey).where(
        ApiKey.org_id == current_user.org_id,
        ApiKey.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "permissions": k.permissions,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in result.scalars().all()
    ]


@router.post("/", status_code=201, dependencies=[Depends(require_role(UserRole.OWNER))])
async def create_api_key(
    name: str,
    db: DbSession,
    current_user: CurrentUser,
    permissions: list[str] | None = None,
) -> dict:
    """Create a new API key. The raw key is shown ONCE."""
    raw_key, key_hash = generate_api_key()
    api_key = ApiKey(
        org_id=current_user.org_id,
        name=name,
        key_hash=key_hash,
        key_prefix=raw_key[:12] + "...",
        permissions=permissions or ["read"],
        created_by_id=current_user.id,
    )
    db.add(api_key)
    await db.flush()
    return {
        "id": str(api_key.id),
        "name": name,
        "key": raw_key,  # Shown ONCE
        "message": "Store this key securely. It cannot be retrieved again.",
    }


@router.delete("/{key_id}", dependencies=[Depends(require_role(UserRole.OWNER))])
async def revoke_api_key(key_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> dict:
    """Revoke an API key."""
    stmt = select(ApiKey).where(
        ApiKey.id == key_id,
        ApiKey.org_id == current_user.org_id,
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise NotFoundError("ApiKey", str(key_id))
    api_key.deleted_at = datetime.now(timezone.utc)
    api_key.is_active = False
    return {"message": "API key revoked."}
