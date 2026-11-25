"""
Subscription Model

Tracks SaaS subscription tiers, limits, and Stripe lifecycle status.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, generate_uuid


class Subscription(Base, TimestampMixin, TenantMixin):
    """
    SaaS Subscription details per Organization.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"  # free, pro, enterprise
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"  # active, trialing, past_due, canceled
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_evaluation_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    monthly_evaluations_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, plan='{self.plan_tier}', status='{self.status}')>"
