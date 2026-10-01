from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_models import Base


class StudentVerificationStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class StudentVerificationApplication(Base):
    __tablename__ = "student_verification_applications"
    __table_args__ = (
        CheckConstraint(
            "length(trim(institution_name)) > 0",
            name="ck_student_verification_institution",
        ),
        Index(
            "uq_student_verification_pending_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
        Index(
            "ix_student_verification_status_created",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(200), nullable=False)
    enrollment_number: Mapped[str] = mapped_column(String(100), nullable=False)
    course_or_program: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(50), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    institution_email: Mapped[str | None] = mapped_column(String(255))
    additional_information: Mapped[str | None] = mapped_column(Text)
    proof_original_filename: Mapped[str | None] = mapped_column(String(255))
    proof_stored_filename: Mapped[str | None] = mapped_column(String(100))
    proof_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    proof_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StudentVerificationStatus] = mapped_column(
        Enum(
            StudentVerificationStatus,
            name="student_verification_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=StudentVerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    admin_reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    admin_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    student_entitlement_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    proof_delete_after: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )
