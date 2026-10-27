from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        CheckConstraint("price_minor >= 0", name="ck_subscription_plans_price_nonnegative"),
        CheckConstraint(
            "currency = upper(currency) AND length(currency) = 3",
            name="ck_subscription_plans_currency",
        ),
        CheckConstraint(
            "billing_interval IN ('monthly', 'yearly')", name="ck_subscription_plans_interval"
        ),
        UniqueConstraint("code", name="uq_subscription_plans_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    price_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default="BDT"
    )
    billing_interval: Mapped[str] = mapped_column(
        String(16), nullable=False, default="monthly", server_default="monthly"
    )
    limits: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class StoreSubscription(Base):
    __tablename__ = "store_subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'past_due', 'canceled')", name="ck_store_subscriptions_status"
        ),
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
