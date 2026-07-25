"""
Prompt Template Model

Reusable prompt templates for evaluation judges.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid


class PromptTemplate(Base, TimestampMixin, TenantMixin):
    """Reusable prompt template for evaluation judges."""

    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    template_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., hallucination_judge, faithfulness_judge
    variables: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
