"""
Provider Config Model

Encrypted tenant-specific configurations for external AI providers (OpenAI, Claude, Gemini, Groq, DeepSeek, Azure, Ollama).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid


class ProviderConfig(Base, TimestampMixin, TenantMixin):
    """
    AI Model Provider Configuration per Tenant/Project.
    """

    __tablename__ = "provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    provider_name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True  # openai, anthropic, google, groq, deepseek, azure_openai, openrouter, ollama
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<ProviderConfig(id={self.id}, provider='{self.provider_name}', is_active={self.is_active})>"
