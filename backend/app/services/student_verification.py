import logging
import os
import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification, NotificationType
from app.models.student_verification import (
    StudentVerificationApplication,
    StudentVerificationStatus,
)
from app.models.user import User

logger = logging.getLogger(__name__)

MAX_PROOF_SIZE = 10 * 1024 * 1024
STUDENT_ACCESS_DURATION = timedelta(days=365)
PROOF_RETENTION = timedelta(days=90)
ALLOWED_PROOF_TYPES = {
    ".pdf": ("application/pdf",),
    ".jpg": ("image/jpeg",),
    ".jpeg": ("image/jpeg",),
    ".png": ("image/png",),
}


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def storage_root() -> Path:
    configured = Path(settings.STUDENT_VERIFICATION_STORAGE_DIR)
    if not configured.is_absolute():
        configured = Path(__file__).resolve().parents[2] / configured
    return configured.resolve()


def proof_path(stored_filename: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}\.(pdf|jpg|jpeg|png)", stored_filename):
        raise HTTPException(status_code=404, detail="Proof document not found.")
    root = storage_root()
    path = (root / stored_filename).resolve()
    if path.parent != root:
        raise HTTPException(status_code=404, detail="Proof document not found.")
    return path


def remove_stored_proof(stored_filename: str) -> None:
    path = proof_path(stored_filename)
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        logger.error(
            "Student verification proof cleanup failed (%s).",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to securely remove the proof document.",
        ) from error


def delete_proof(application: StudentVerificationApplication) -> None:
    if not application.proof_stored_filename:
        return
    remove_stored_proof(application.proof_stored_filename)
    application.proof_stored_filename = None
    application.proof_original_filename = None
    application.proof_size = 0
    application.proof_content_type = "application/octet-stream"


def cleanup_expired_proofs(db: Session) -> None:
    expired = (
        db.query(StudentVerificationApplication)
        .filter(
            StudentVerificationApplication.status
            != StudentVerificationStatus.PENDING,
            StudentVerificationApplication.proof_delete_after <= utcnow_naive(),
            StudentVerificationApplication.proof_stored_filename.is_not(None),
        )
        .all()
    )
    if not expired:
        return
    for application in expired:
        delete_proof(application)
    db.commit()


def _validate_proof(name: str, content_type: str, data: bytes) -> str:
    extension = Path(name).suffix.lower()
    expected_types = ALLOWED_PROOF_TYPES.get(extension)
    if not expected_types or content_type.lower() not in expected_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PDF, JPEG, or PNG proof document.",
        )

    valid_signature = False
    if extension == ".pdf":
        valid_signature = b"%PDF-" in data[:1024]
    elif extension in {".jpg", ".jpeg"}:
        valid_signature = data.startswith(b"\xff\xd8\xff")
    elif extension == ".png":
        valid_signature = data.startswith(b"\x89PNG\r\n\x1a\n")
    if not valid_signature:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file does not match its declared document type.",
        )
    return extension


def _notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    application_id: int,
) -> None:
    db.add(
        Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url="/dashboard/student-verification",
            metadata_json=f'{{"student_verification_application_id":{application_id}}}',
        )
    )


def application_response(
    application: StudentVerificationApplication,
    *,
    include_admin_fields: bool = False,
) -> dict:
    response = {
        "id": application.id,
        "applicant_name": application.applicant_name,
        "institution_name": application.institution_name,
        "course_or_program": application.course_or_program,
        "academic_year": application.academic_year,
        "graduation_year": application.graduation_year,
        "institution_email": application.institution_email,
        "additional_information": application.additional_information,
        "status": application.status.value,
        "created_at": application.created_at.isoformat(),
        "admin_reviewed_at": (
            application.admin_reviewed_at.isoformat()
            if application.admin_reviewed_at
            else None
        ),
        "rejection_reason": application.rejection_reason,
        "student_entitlement_expires_at": (
            application.student_entitlement_expires_at.isoformat()
            if application.student_entitlement_expires_at
            else None
        ),
        "proof_available": bool(application.proof_stored_filename),
    }
    if include_admin_fields:
        response.update(
            {
                "user_id": application.user_id,
                "enrollment_number": application.enrollment_number,
                "proof_original_filename": application.proof_original_filename,
                "proof_content_type": application.proof_content_type,
                "proof_size": application.proof_size,
                "admin_reviewed_by": application.admin_reviewed_by,
            }
        )
    return response


async def persist_proof(upload: UploadFile) -> tuple[str, str, int, str]:
    supplied_name = (upload.filename or "").replace("\\", "/")
    original_name = supplied_name.rsplit("/", 1)[-1].replace("\x00", "")[:255]
    if not original_name:
        raise HTTPException(status_code=400, detail="A proof filename is required.")
    content_type = (upload.content_type or "").split(";", 1)[0].strip().lower()
    data = await upload.read(MAX_PROOF_SIZE + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The proof document is empty.")
    if len(data) > MAX_PROOF_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Proof documents must be 10 MB or smaller.",
        )
    extension = _validate_proof(original_name, content_type, data)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    root = storage_root()
    path = proof_path(stored_name)
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            root.chmod(0o700)
        file_descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(file_descriptor, "wb") as proof_file:
            proof_file.write(data)
    except OSError as error:
        try:
            path.unlink(missing_ok=True)
        except OSError as cleanup_error:
            logger.error(
                "Partial student verification proof cleanup failed (%s).",
                type(cleanup_error).__name__,
            )
        logger.error(
            "Student verification proof storage failed (%s).",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the proof document.",
        ) from error
    return original_name, stored_name, len(data), content_type


def maybe_notify_entitlement_events(
    db: Session,
    user_id: int,
    application: StudentVerificationApplication | None,
) -> None:
    if (
        application is None
        or application.status != StudentVerificationStatus.APPROVED
        or application.student_entitlement_expires_at is None
    ):
        return
    now = utcnow_naive()
    expires_at = application.student_entitlement_expires_at
    if expires_at <= now:
        title = "Student Pro access expired"
        message = "Your student Pro access has expired."
        notification_type = NotificationType.WARNING
    elif expires_at - now <= timedelta(days=30):
        title = "Student Pro access expires soon"
        message = "Your student Pro access will expire within 30 days."
        notification_type = NotificationType.INFO
    else:
        return
    exists = (
        db.query(Notification.id)
        .filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.metadata_json
            == f'{{"student_verification_application_id":{application.id}}}',
        )
        .first()
    )
    if not exists:
        _notification(
            db,
            user_id,
            title,
            message,
            notification_type,
            application.id,
        )
        db.commit()
