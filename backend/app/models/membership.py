"""
Membership Model

Manages user role-based access control (RBAC) within an organization.
Supported roles: Owner, Admin, Developer, Viewer.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class RoleEnum(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class Membership(Base, TimestampMixin):
    """
    Membership maps a User to an Organization with a designated RBAC Role.
    """

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_user_organization"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=RoleEnum.DEVELOPER.value, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    organization: Mapped["Organization"] = relationship("Organization", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Membership(id={self.id}, user_id={self.user_id}, org_id={self.org_id}, role='{self.role}')>"
