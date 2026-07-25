"""
Latency Record Model

Stores detailed latency breakdown per question.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationResult


class LatencyRecord(Base, TimestampMixin):
    """Detailed latency breakdown for a single question."""

    __tablename__ = "latency_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_ms: Mapped[float] = mapped_column(Float, nullable=False)
    ttfb_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    network_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
