"""
Vector Database Configuration Model

Stores per-project vector database connection settings.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.project import Project


class VectorDBConfig(Base, TimestampMixin, TenantMixin):
    """
    Vector database connection configuration for a project.

    Connection credentials are stored encrypted.
    """

    __tablename__ = "vector_db_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )

    # Connection settings (provider-specific)
    connection_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    # Encrypted connection string / API key
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Collection / index name
    collection_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    index_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Embedding settings
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="vector_db_configs"
    )

    def __repr__(self) -> str:
        return (
            f"<VectorDBConfig(id={self.id}, provider='{self.provider_type}')>"
        )
