"""
Metric Model

Stores individual evaluator scores for each question result.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationResult


class Metric(Base, TimestampMixin):
    """A single evaluator score for a question result."""

    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluator_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")

    # Relationships
    evaluation_result: Mapped["EvaluationResult"] = relationship(
        "EvaluationResult", back_populates="metrics"
    )
