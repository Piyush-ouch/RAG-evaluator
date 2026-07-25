"""
Evaluation & EvaluationResult Models

An Evaluation represents a complete benchmark run.
EvaluationResult stores per-question responses and scores.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.benchmark import BenchmarkSuite
    from app.models.cost import CostRecord
    from app.models.metric import Metric
    from app.models.project import Project
    from app.models.report import Report
    from app.models.retrieved_chunk import RetrievedChunk
    from app.models.security_finding import SecurityFinding


class Evaluation(Base, TimestampMixin, TenantMixin):
    """
    An evaluation run — executing a benchmark suite against a chatbot.

    Tracks lifecycle from PENDING → RUNNING → COMPLETED/FAILED/CANCELLED.
    """

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("benchmark_suites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )
    version_tag: Mapped[str | None] = mapped_column(
        String(100), nullable=True  # For version comparison, e.g., "v1.2.0"
    )

    # Progress tracking
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Aggregated scores (computed after completion)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    faithfulness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p50_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p95_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p99_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Configuration snapshot (so we know what was tested)
    config_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Evaluator configuration (which evaluators to run)
    enabled_evaluators: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Triggered by
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="evaluations"
    )
    benchmark_suite: Mapped["BenchmarkSuite"] = relationship(
        "BenchmarkSuite", back_populates="evaluations"
    )
    results: Mapped[list["EvaluationResult"]] = relationship(
        "EvaluationResult", back_populates="evaluation", lazy="selectin",
        cascade="all, delete-orphan"
    )
    cost_records: Mapped[list["CostRecord"]] = relationship(
        "CostRecord", back_populates="evaluation", lazy="selectin",
        cascade="all, delete-orphan"
    )
    security_findings: Mapped[list["SecurityFinding"]] = relationship(
        "SecurityFinding", back_populates="evaluation", lazy="selectin",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="evaluation", lazy="selectin",
        cascade="all, delete-orphan"
    )

    @property
    def progress_percent(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round(
            (self.completed_questions / self.total_questions) * 100, 1
        )

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, status='{self.status}', progress={self.progress_percent}%)>"


class EvaluationResult(Base, TimestampMixin):
    """
    Per-question evaluation result.

    Stores the chatbot's response, retrieved context, and all metric scores.
    """

    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chatbot response
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token usage
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Aggregated score for this question
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation", back_populates="results"
    )
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(
        "RetrievedChunk", back_populates="evaluation_result", lazy="selectin",
        cascade="all, delete-orphan"
    )
    metrics: Mapped[list["Metric"]] = relationship(
        "Metric", back_populates="evaluation_result", lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EvaluationResult(id={self.id}, status='{self.status}')>"
