"""
LLM Provider Configuration Model

Stores per-project LLM provider settings with encrypted API keys.
Supports all 8 LLM providers via the provider_type discriminator.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.project import Project


class LLMProviderConfig(Base, TimestampMixin, TenantMixin):
    """
    LLM provider configuration for a project.

    API keys are stored encrypted via Fernet.
    Multiple providers can be configured per project (e.g., one for the chatbot,
    one for the evaluation judge).
    """

    __tablename__ = "llm_provider_configs"

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
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provider-specific settings
    api_base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    api_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deployment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Model parameters
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Usage tracking
    is_judge: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Whether this provider is used as the evaluation judge
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Extra settings (headers, custom params)
    extra_settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="llm_configs"
    )

    def __repr__(self) -> str:
        return (
            f"<LLMProviderConfig(id={self.id}, provider='{self.provider_type}', "
            f"model='{self.model_name}')>"
        )
