"""add student verification applications

Revision ID: 20261001_student_verification
Revises: 20260928_auth_invoices
Create Date: 2026-10-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20261001_student_verification"
down_revision = "20260928_auth_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_type = sa.Enum(
        "pending",
        "approved",
        "rejected",
        "withdrawn",
        name="student_verification_status",
        native_enum=False,
        create_constraint=True,
    )
    op.create_table(
        "student_verification_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("applicant_name", sa.String(100), nullable=False),
        sa.Column("institution_name", sa.String(200), nullable=False),
        sa.Column("enrollment_number", sa.String(100), nullable=False),
        sa.Column("course_or_program", sa.String(200), nullable=False),
        sa.Column("academic_year", sa.String(50), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("institution_email", sa.String(255), nullable=True),
        sa.Column("additional_information", sa.Text(), nullable=True),
        sa.Column("proof_original_filename", sa.String(255), nullable=True),
        sa.Column("proof_stored_filename", sa.String(100), nullable=True),
        sa.Column("proof_content_type", sa.String(100), nullable=False),
        sa.Column("proof_size", sa.Integer(), nullable=False),
        sa.Column("status", status_type, nullable=False, server_default="pending"),
        sa.Column(
            "admin_reviewed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("admin_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("student_entitlement_expires_at", sa.DateTime(), nullable=True),
        sa.Column("proof_delete_after", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "length(trim(institution_name)) > 0",
            name="ck_student_verification_institution",
        ),
    )
    op.create_index(
        "ix_student_verification_applications_user_id",
        "student_verification_applications",
        ["user_id"],
    )
    op.create_index(
        "ix_student_verification_applications_status",
        "student_verification_applications",
        ["status"],
    )
    op.create_index(
        "ix_student_verification_status_created",
        "student_verification_applications",
        ["status", "created_at"],
    )
    op.create_index(
        "uq_student_verification_pending_user",
        "student_verification_applications",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_student_verification_pending_user",
        table_name="student_verification_applications",
    )
    op.drop_index(
        "ix_student_verification_status_created",
        table_name="student_verification_applications",
    )
    op.drop_index(
        "ix_student_verification_applications_status",
        table_name="student_verification_applications",
    )
    op.drop_index(
        "ix_student_verification_applications_user_id",
        table_name="student_verification_applications",
    )
    op.drop_table("student_verification_applications")
