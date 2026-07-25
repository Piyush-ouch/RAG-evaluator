"""
Organization Model

The root tenant entity. All resources (users, projects, benchmarks, etc.)
belong to an organization. Multi-tenancy is enforced by filtering on org_id.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.billing import BillingAccount
    from app.models.project import Project
    from app.models.user import User


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """
    Organization — the top-level tenant entity.

    Every user belongs to an organization. All data is isolated per organization.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free", index=True
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Stripe integration
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", lazy="selectin"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="organization", lazy="selectin"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="organization", lazy="selectin"
    )
    billing_account: Mapped["BillingAccount | None"] = relationship(
        "BillingAccount", back_populates="organization", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"
