"""merge migration heads

Revision ID: 658de0610bd9
Revises: 55aa91c462ea, a1b2c3d4e5f6
Create Date: 2026-09-09 11:25:24.021243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '658de0610bd9'
down_revision: Union[str, Sequence[str], None] = ('55aa91c462ea', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
