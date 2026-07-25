"""
Retrieved Chunk Model

Stores the context chunks retrieved by the RAG system for each question.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationResult


class RetrievedChunk(Base, TimestampMixin):
    """A single context chunk retrieved by the RAG system."""

    __tablename__ = "retrieved_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    evaluation_result: Mapped["EvaluationResult"] = relationship(
        "EvaluationResult", back_populates="retrieved_chunks"
    )
