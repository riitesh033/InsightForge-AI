"""add rows and columns to datasets

Revision ID: 3523d78a50b6
Revises: 68daab538788
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "3523d78a50b6"
down_revision = "68daab538788"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "datasets",
        sa.Column(
            "rows",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "datasets",
        sa.Column(
            "columns",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade():
    op.drop_column("datasets", "columns")
    op.drop_column("datasets", "rows")