"""add the invoices primary-key index declared by the model

Revision ID: 20261007_invoice_id_index
Revises: 20261001_student_verification
"""

from alembic import op


revision = "20261007_invoice_id_index"
down_revision = "20261001_student_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_invoices_id", "invoices", ["id"])


def downgrade() -> None:
    op.drop_index("ix_invoices_id", table_name="invoices")
