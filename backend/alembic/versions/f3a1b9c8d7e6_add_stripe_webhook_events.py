"""add persistent Stripe webhook idempotency records

Revision ID: f3a1b9c8d7e6
Revises: 42420889e6ec
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


revision = "f3a1b9c8d7e6"
down_revision = "42420889e6ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_stripe_webhook_events_event_type",
        "stripe_webhook_events",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stripe_webhook_events_event_type",
        table_name="stripe_webhook_events",
    )
    op.drop_table("stripe_webhook_events")
