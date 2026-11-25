"""
Target Application Connection Model

Represents configuration parameters to connect and invoke target Chatbots, AI Agents, or MCP Servers.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.project import Project


class Connection(Base, TimestampMixin, TenantMixin):
    """
    Target RAG System / AI Agent Connection Configuration.
    """

    __tablename__ = "connections"

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
    connection_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="http_rest"  # http_rest, mcp_server, websocket, gRPC
    )
    endpoint_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False, default="POST")
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    request_template: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(default=30, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    project: Mapped["Project"] = relationship("Project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, name='{self.name}', type='{self.connection_type}', url='{self.endpoint_url}')>"
