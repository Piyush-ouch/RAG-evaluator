"""
Vector Database Configuration Model

Tenant-specific Vector DB configurations (Qdrant, Pinecone, Chroma, FAISS, Weaviate, Milvus, PgVector).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid


class VectorConfig(Base, TimestampMixin, TenantMixin):
    """
    Vector DB Provider Integration settings.
    """

    __tablename__ = "vector_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    provider_name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True  # qdrant, pinecone, chroma, faiss, weaviate, milvus, pgvector
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    host: Mapped[str | None] = mapped_column(String(512), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    collection_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extra_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<VectorConfig(id={self.id}, provider='{self.provider_name}', collection='{self.collection_name}')>"
