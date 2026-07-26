"""
Project Model

Projects are the central workspace where users configure their RAG system,
connect their AI API, choose LLM/VectorDB providers, and run evaluations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.benchmark import BenchmarkSuite
    from app.models.evaluation import Evaluation
    from app.models.llm_provider import LLMProviderConfig
    from app.models.organization import Organization
    from app.models.vector_db import VectorDBConfig


class Project(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    """
    Project — a workspace for evaluating a specific RAG system.

    Each project connects to one AI chatbot API and can have multiple
    benchmark suites and evaluations.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Customer's RAG chatbot API endpoint
    chatbot_api_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chatbot_api_key_encrypted: Mapped[str | None] = mapped_column(
        Text, nullable=True  # Fernet-encrypted
    )
    chatbot_api_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    chatbot_api_method: Mapped[str] = mapped_column(
        String(10), nullable=False, default="POST"
    )
    chatbot_request_template: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True  # JSON template for request body
    )
    chatbot_response_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True  # JSONPath to extract response text
    )

    # Project settings
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Foreign key to organization
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Created by
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )


    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="projects"
    )
    llm_configs: Mapped[list["LLMProviderConfig"]] = relationship(
        "LLMProviderConfig", back_populates="project", lazy="selectin",
        cascade="all, delete-orphan"
    )
    vector_db_configs: Mapped[list["VectorDBConfig"]] = relationship(
        "VectorDBConfig", back_populates="project", lazy="selectin",
        cascade="all, delete-orphan"
    )
    benchmark_suites: Mapped[list["BenchmarkSuite"]] = relationship(
        "BenchmarkSuite", back_populates="project", lazy="selectin",
        cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="project", lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
