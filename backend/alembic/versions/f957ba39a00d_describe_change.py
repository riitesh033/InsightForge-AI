"""historical no-op bridge before analyses table

Revision ID: f957ba39a00d
Revises: 3523d78a50b6
Create Date: 2026-08-06
"""

from alembic import op


revision = "f957ba39a00d"
down_revision = "3523d78a50b6"
branch_labels = None
depends_on = None


def upgrade():
    """Keep this historical revision in the graph without schema changes."""
    pass


def downgrade():
    """Keep downgrade behavior aligned with the no-op upgrade."""
    pass