"""historical no-op revision before analysis summary fields

Revision ID: c29672287d79
Revises: 48e8bbad6175
Create Date: 2026-07-31 16:52:15.002107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c29672287d79'
down_revision: Union[str, Sequence[str], None] = '48e8bbad6175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Keep this historical revision in the graph without schema changes."""
    pass


def downgrade() -> None:
    """Keep downgrade behavior aligned with the no-op upgrade."""
    pass
