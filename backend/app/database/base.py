"""
SQLAlchemy Declarative Base & Mixins

Provides:
- Base class for all ORM models
- TimestampMixin: created_at, updated_at
- TenantMixin: org_id with automatic filtering
- SoftDeleteMixin: deleted_at for soft deletes
- Common column types and index helpers
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Provides:
    - UUID primary key generation
    - Type annotation support (mapped_column)
    - Consistent naming convention for constraints
    """

    metadata = MetaData(naming_convention=naming_convention)


class TimestampMixin:
    """Adds created_at and updated_at columns with automatic timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    """
    Adds org_id column for multi-tenant isolation.

    All tenant-scoped models inherit from this mixin.
    """

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    """Adds deleted_at column for soft-delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


def generate_uuid() -> uuid.UUID:
    """Generate a v4 UUID."""
    return uuid.uuid4()
