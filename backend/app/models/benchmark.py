"""
Benchmark Suite & Question Models

Benchmark suites are collections of questions organized by domain.
Questions contain the test input, expected output, and metadata.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.project import Project


class BenchmarkSuite(Base, TimestampMixin, TenantMixin):
    """
    A collection of benchmark questions organized by domain.

    Suites can be built-in templates or custom user uploads.
    """

    __tablename__ = "benchmark_suites"

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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_template: Mapped[bool] = mapped_column(default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Source dataset provenance
    source_dataset: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    source_subset: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="benchmark_suites"
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="benchmark_suite", lazy="selectin",
        cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="benchmark_suite", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<BenchmarkSuite(id={self.id}, name='{self.name}', domain='{self.domain}')>"


class Question(Base, TimestampMixin):
    """
    A single benchmark question within a suite.

    Contains the question text, expected answer (ground truth),
    category, difficulty, and any additional metadata.
    """

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    suite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("benchmark_suites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )
    evaluation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="rag"
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Source dataset provenance
    source_dataset: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    source_subset: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    source_question_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    dataset_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1.0"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Expected context — for evaluating retrieval quality
    expected_context: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Expected citations
    expected_citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Tags and metadata
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    benchmark_suite: Mapped["BenchmarkSuite"] = relationship(
        "BenchmarkSuite", back_populates="questions"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, text='{self.text[:50]}...')>"
