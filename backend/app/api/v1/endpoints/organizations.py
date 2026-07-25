"""
Organization API Endpoints
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.models.organization import Organization
from app.schemas.project import OrganizationCreate, OrganizationResponse, OrganizationUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    db: DbSession,
    current_user: CurrentUser,
) -> list[OrganizationResponse]:
    """List organizations the current user belongs to."""
    stmt = select(Organization).where(
        Organization.id == current_user.org_id,
        Organization.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    orgs = result.scalars().all()
    return [OrganizationResponse.model_validate(o, from_attributes=True) for o in orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> OrganizationResponse:
    """Get organization details."""
    import uuid
    stmt = select(Organization).where(
        Organization.id == uuid.UUID(org_id),
        Organization.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", org_id)
    return OrganizationResponse.model_validate(org, from_attributes=True)


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_role(UserRole.OWNER))],
)
async def update_organization(
    org_id: str,
    request: OrganizationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OrganizationResponse:
    """Update organization details. Requires Owner role."""
    import uuid
    stmt = select(Organization).where(
        Organization.id == uuid.UUID(org_id),
        Organization.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", org_id)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)

    return OrganizationResponse.model_validate(org, from_attributes=True)
