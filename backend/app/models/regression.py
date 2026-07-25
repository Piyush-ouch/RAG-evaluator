"""
Regression History Model

Tracks version-over-version evaluation comparisons.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid


class RegressionHistory(Base, TimestampMixin, TenantMixin):
    """Comparison between two evaluation runs for regression detection."""

    __tablename__ = "regression_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    eval_baseline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    eval_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    baseline_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    candidate_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Score deltas (positive = improvement, negative = regression)
    overall_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    faithfulness_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Detailed per-question comparison
    diff_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(nullable=True)
    has_regression: Mapped[bool] = mapped_column(default=False, nullable=False)
