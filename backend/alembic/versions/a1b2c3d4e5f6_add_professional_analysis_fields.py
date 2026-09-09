"""add professional analysis fields

Revision ID: a1b2c3d4e5f6
Revises: 0179eb8e1705
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '0179eb8e1705'
branch_labels = None
depends_on = None


def upgrade():
    # Add executive_summary column
    op.add_column('analyses', sa.Column('executive_summary', sa.Text(), nullable=True))
    
    # Add key_insights column
    op.add_column('analyses', sa.Column('key_insights', sa.JSON(), nullable=True))
    
    # Add recommendations column
    op.add_column('analyses', sa.Column('recommendations', sa.JSON(), nullable=True))
    
    # Add business_opportunities column
    op.add_column('analyses', sa.Column('business_opportunities', sa.JSON(), nullable=True))
    
    # Add distributions column
    op.add_column('analyses', sa.Column('distributions', sa.JSON(), nullable=True))
    
    # Add data_quality_issues column
    op.add_column('analyses', sa.Column('data_quality_issues', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('analyses', 'data_quality_issues')
    op.drop_column('analyses', 'distributions')
    op.drop_column('analyses', 'business_opportunities')
    op.drop_column('analyses', 'recommendations')
    op.drop_column('analyses', 'key_insights')
    op.drop_column('analyses', 'executive_summary')
