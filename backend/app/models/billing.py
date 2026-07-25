"""
Billing Models

Billing account with Stripe integration and usage tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, generate_uuid


class BillingAccount(Base, TimestampMixin):
    """Organization billing account linked to Stripe."""

    __tablename__ = "billing_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    billing_interval: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Trial
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_trial_active: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Current period
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Usage limits
    evaluation_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    evaluations_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # type: ignore
        "Organization", back_populates="billing_account"
    )
    usage_records: Mapped[list["BillingUsage"]] = relationship(
        "BillingUsage", back_populates="billing_account", lazy="selectin",
        cascade="all, delete-orphan"
    )


class BillingUsage(Base, TimestampMixin):
    """Monthly usage record for metered billing."""

    __tablename__ = "billing_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid
    )
    billing_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    evaluations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    api_calls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    usage_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    billing_account: Mapped["BillingAccount"] = relationship(
        "BillingAccount", back_populates="usage_records"
    )
