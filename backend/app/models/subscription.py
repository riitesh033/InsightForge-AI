from datetime import UTC, datetime
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_models import Base


class PlanType(str, PyEnum):
    """Plan values are lowercase: they match the Stripe plan ids used by the
    payment service (``plan_type="free"/"pro"/"business"``) and the existing
    database rows written before this fix (VARCHAR(20) with lowercase values)."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionStatus(str, PyEnum):
    """Status values are lowercase and use Stripe's spelling (``incomplete_expired``)
    so that ``SubscriptionStatus(stripe_subscription["status"])`` from the webhook
    handler never raises ValueError. The DB enum name is pinned to
    ``subscription_status`` to match the original migration."""

    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    PAUSED = "paused"


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan: Mapped[str] = mapped_column(
        Enum(PlanType, name="plan_type", values_callable=lambda e: [m.value for m in e]),
        default=PlanType.FREE,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscription_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    provider_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscription",
    )

    payment_history: Mapped[list["PaymentHistory"]] = relationship(
        "PaymentHistory",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    payment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    payment_provider: Mapped[str] = mapped_column(
        String(50),
        default="stripe",
        nullable=False,
    )

    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    plan_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        nullable=False,
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="payment_history",
    )


class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    event_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )
