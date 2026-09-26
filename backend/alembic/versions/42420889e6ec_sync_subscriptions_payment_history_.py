"""sync subscriptions/payment_history/notifications schema with models

The original migration 20240901abc12 created these tables as plain VARCHAR
columns, but the SQLAlchemy models use enums (plan_type, subscription_status,
notification_type), several indexed columns and additional fields
(provider_customer_id, payment_provider, metadata_json, expires_at).

This revision reconciles the database with the models:

* adds missing columns (with server defaults so existing rows survive)
* converts VARCHAR columns to native PostgreSQL enums via USING casts
* narrows/widens string types where the model is authoritative
* adds missing indexes and unique constraints (named explicitly)

Revision ID: 42420889e6ec
Revises: 20240901abc12
Create Date: 2026-09-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42420889e6ec'
down_revision: Union[str, Sequence[str], None] = '20240901abc12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLAN_TYPE = sa.Enum('free', 'pro', 'business', name='plan_type')
SUBSCRIPTION_STATUS = sa.Enum(
    'active', 'canceled', 'incomplete', 'incomplete_expired',
    'trialing', 'past_due', 'unpaid', 'paused',
    name='subscription_status',
)
NOTIFICATION_TYPE = sa.Enum(
    'info', 'success', 'warning', 'error', 'payment', 'system',
    name='notification_type',
)


def upgrade() -> None:
    # --- notifications -----------------------------------------------------
    op.add_column('notifications', sa.Column('metadata_json', sa.Text(), nullable=True))
    op.add_column('notifications', sa.Column('expires_at', sa.DateTime(), nullable=True))
    op.alter_column('notifications', 'title',
                    existing_type=sa.VARCHAR(length=255),
                    type_=sa.String(length=200),
                    existing_nullable=False)
    # type: VARCHAR(30) default 'info' -> notification_type enum.
    # Drop the varchar default first; PostgreSQL cannot auto-cast the old
    # column default when changing the column type.
    op.alter_column('notifications', 'type',
                    existing_type=sa.VARCHAR(length=30),
                    server_default=None,
                    existing_nullable=False)
    NOTIFICATION_TYPE.create(op.get_bind(), checkfirst=True)
    op.alter_column('notifications', 'type',
                    existing_type=sa.VARCHAR(length=30),
                    type_=NOTIFICATION_TYPE,
                    existing_nullable=False,
                    postgresql_using='type::text::notification_type')
    op.alter_column('notifications', 'type',
                    existing_type=NOTIFICATION_TYPE,
                    server_default='info',
                    existing_nullable=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)

    # --- payment_history ---------------------------------------------------
    op.add_column('payment_history',
                  sa.Column('payment_provider', sa.String(length=50),
                            nullable=False, server_default='stripe'))
    op.add_column('payment_history', sa.Column('metadata_json', sa.Text(), nullable=True))
    op.alter_column('payment_history', 'currency',
                    existing_type=sa.VARCHAR(length=10),
                    type_=sa.String(length=3),
                    existing_nullable=False,
                    existing_server_default=sa.text("'USD'::character varying"))
    op.alter_column('payment_history', 'payment_status',
                    existing_type=sa.VARCHAR(length=30),
                    type_=sa.String(length=50),
                    existing_nullable=False)
    op.alter_column('payment_history', 'plan_type',
                    existing_type=sa.VARCHAR(length=20),
                    type_=sa.String(length=50),
                    existing_nullable=False)
    op.alter_column('payment_history', 'description',
                    existing_type=sa.VARCHAR(length=500),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.create_index(op.f('ix_payment_history_payment_status'), 'payment_history', ['payment_status'], unique=False)
    op.create_index(op.f('ix_payment_history_subscription_id'), 'payment_history', ['subscription_id'], unique=False)
    op.create_unique_constraint('uq_payment_history_provider_payment_id',
                                'payment_history', ['provider_payment_id'])

    # --- subscriptions -----------------------------------------------------
    op.add_column('subscriptions',
                  sa.Column('provider_customer_id', sa.String(length=255), nullable=True))
    # plan/status: VARCHAR -> native enums. Drop the varchar defaults first;
    # PostgreSQL cannot auto-cast an old column default when changing type.
    op.alter_column('subscriptions', 'plan',
                    existing_type=sa.VARCHAR(length=20),
                    server_default=None,
                    existing_nullable=False)
    op.alter_column('subscriptions', 'status',
                    existing_type=sa.VARCHAR(length=20),
                    server_default=None,
                    existing_nullable=False)
    PLAN_TYPE.create(op.get_bind(), checkfirst=True)
    op.alter_column('subscriptions', 'plan',
                    existing_type=sa.VARCHAR(length=20),
                    type_=PLAN_TYPE,
                    existing_nullable=False,
                    postgresql_using='plan::text::plan_type')
    op.alter_column('subscriptions', 'plan',
                    existing_type=PLAN_TYPE,
                    server_default='free',
                    existing_nullable=False)
    SUBSCRIPTION_STATUS.create(op.get_bind(), checkfirst=True)
    op.alter_column('subscriptions', 'status',
                    existing_type=sa.VARCHAR(length=20),
                    type_=SUBSCRIPTION_STATUS,
                    existing_nullable=False,
                    postgresql_using='status::text::subscription_status')
    op.alter_column('subscriptions', 'status',
                    existing_type=SUBSCRIPTION_STATUS,
                    server_default='active',
                    existing_nullable=False)
    op.create_index(op.f('ix_subscriptions_provider_customer_id'), 'subscriptions', ['provider_customer_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)
    op.create_unique_constraint('uq_subscriptions_provider_subscription_id',
                                'subscriptions', ['provider_subscription_id'])


def downgrade() -> None:
    # --- subscriptions -----------------------------------------------------
    op.drop_constraint('uq_subscriptions_provider_subscription_id', 'subscriptions', type_='unique')
    op.drop_index(op.f('ix_subscriptions_status'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_provider_customer_id'), table_name='subscriptions')
    op.alter_column('subscriptions', 'status',
                    existing_type=SUBSCRIPTION_STATUS,
                    type_=sa.VARCHAR(length=20),
                    existing_nullable=False,
                    server_default='active',
                    postgresql_using='status::text')
    op.alter_column('subscriptions', 'plan',
                    existing_type=PLAN_TYPE,
                    type_=sa.VARCHAR(length=20),
                    existing_nullable=False,
                    server_default='free',
                    postgresql_using='plan::text')
    op.drop_column('subscriptions', 'provider_customer_id')

    # --- payment_history ---------------------------------------------------
    op.drop_constraint('uq_payment_history_provider_payment_id', 'payment_history', type_='unique')
    op.drop_index(op.f('ix_payment_history_subscription_id'), table_name='payment_history')
    op.drop_index(op.f('ix_payment_history_payment_status'), table_name='payment_history')
    op.alter_column('payment_history', 'description',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=500),
                    existing_nullable=True)
    op.alter_column('payment_history', 'plan_type',
                    existing_type=sa.String(length=50),
                    type_=sa.VARCHAR(length=20),
                    existing_nullable=False)
    op.alter_column('payment_history', 'payment_status',
                    existing_type=sa.String(length=50),
                    type_=sa.VARCHAR(length=30),
                    existing_nullable=False)
    op.alter_column('payment_history', 'currency',
                    existing_type=sa.String(length=3),
                    type_=sa.VARCHAR(length=10),
                    existing_nullable=False,
                    existing_server_default=sa.text("'USD'::character varying"))
    op.drop_column('payment_history', 'metadata_json')
    op.drop_column('payment_history', 'payment_provider')

    # --- notifications -----------------------------------------------------
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.alter_column('notifications', 'type',
                    existing_type=NOTIFICATION_TYPE,
                    type_=sa.VARCHAR(length=30),
                    existing_nullable=False,
                    server_default='info',
                    postgresql_using='type::text')
    op.alter_column('notifications', 'title',
                    existing_type=sa.String(length=200),
                    type_=sa.VARCHAR(length=255),
                    existing_nullable=False)
    op.drop_column('notifications', 'expires_at')
    op.drop_column('notifications', 'metadata_json')
