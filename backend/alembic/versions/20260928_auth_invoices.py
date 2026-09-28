"""add Google identity fields and purchase invoices"""

from alembic import op
import sqlalchemy as sa

revision = "20260928_auth_invoices"
down_revision = "f3a1b9c8d7e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_history_id", sa.Integer(), sa.ForeignKey("payment_history.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_number", sa.String(64), nullable=False, unique=True),
        sa.Column("provider_payment_id", sa.String(255), nullable=False, unique=True),
        sa.Column("plan_type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("invoice_date", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("pdf_data", sa.LargeBinary(), nullable=False),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_invoices_user_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "google_id")
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)
