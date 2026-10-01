from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin_user
from app.db.database import get_db
from app.models.notification import NotificationType
from app.models.student_verification import (
    StudentVerificationApplication,
    StudentVerificationStatus,
)
from app.models.user import User
from app.schemas.student_verification import RejectStudentApplicationRequest
from app.services.email import EmailService
from app.services.student_verification import (
    PROOF_RETENTION,
    STUDENT_ACCESS_DURATION,
    _notification,
    application_response,
    cleanup_expired_proofs,
    proof_path,
    utcnow_naive,
)

router = APIRouter()


def _load_application(db: Session, application_id: int):
    return (
        db.query(StudentVerificationApplication)
        .filter(StudentVerificationApplication.id == application_id)
        .with_for_update()
        .first()
    )


def _admin_application_response(
    db: Session, application: StudentVerificationApplication
) -> dict:
    result = application_response(application, include_admin_fields=True)
    user = db.query(User).filter(User.id == application.user_id).first()
    result["user_email"] = user.email if user else None
    return result


@router.get("")
def list_student_applications(
    status_filter: StudentVerificationStatus | None = Query(
        None, alias="status"
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    cleanup_expired_proofs(db)
    query = db.query(StudentVerificationApplication)
    if status_filter is not None:
        query = query.filter(
            StudentVerificationApplication.status == status_filter
        )
    total = query.count()
    applications = (
        query.order_by(
            StudentVerificationApplication.created_at.desc(),
            StudentVerificationApplication.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "applications": [
            _admin_application_response(db, application)
            for application in applications
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{application_id}")
def get_student_application(
    application_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    cleanup_expired_proofs(db)
    application = (
        db.query(StudentVerificationApplication)
        .filter(StudentVerificationApplication.id == application_id)
        .first()
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _admin_application_response(db, application)


@router.get("/{application_id}/proof")
def get_student_application_proof(
    application_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    cleanup_expired_proofs(db)
    application = (
        db.query(StudentVerificationApplication)
        .filter(StudentVerificationApplication.id == application_id)
        .first()
    )
    if application is None or not application.proof_stored_filename:
        raise HTTPException(status_code=404, detail="Proof document not found.")
    path = proof_path(application.proof_stored_filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Proof document not found.")
    return FileResponse(
        path=path,
        media_type=application.proof_content_type,
        filename="student-proof" + path.suffix,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{application_id}/approve")
async def approve_student_application(
    application_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    application = _load_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    if application.status == StudentVerificationStatus.APPROVED:
        return _admin_application_response(db, application)
    if application.status != StudentVerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending applications can be approved.",
        )

    now = utcnow_naive()
    application.status = StudentVerificationStatus.APPROVED
    application.admin_reviewed_by = admin.id
    application.admin_reviewed_at = now
    application.student_entitlement_expires_at = now + STUDENT_ACCESS_DURATION
    application.proof_delete_after = now + PROOF_RETENTION
    application.rejection_reason = None
    _notification(
        db,
        application.user_id,
        "Student verification approved",
        "Your student verification was approved. Student Pro access is active for 365 days.",
        NotificationType.SUCCESS,
        application.id,
    )
    user = db.query(User).filter(User.id == application.user_id).first()
    db.commit()
    db.refresh(application)
    if user is not None:
        await EmailService().send_student_verification_email(
            user.email,
            application.applicant_name,
            "approved",
        )
    return _admin_application_response(db, application)


@router.post("/{application_id}/reject")
async def reject_student_application(
    application_id: int,
    payload: RejectStudentApplicationRequest = Body(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    reason = payload.rejection_reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="A rejection reason is required.")
    application = _load_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    if application.status == StudentVerificationStatus.REJECTED:
        if application.rejection_reason == reason:
            return _admin_application_response(db, application)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This application has already been rejected.",
        )
    if application.status != StudentVerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending applications can be rejected.",
        )

    now = utcnow_naive()
    application.status = StudentVerificationStatus.REJECTED
    application.admin_reviewed_by = admin.id
    application.admin_reviewed_at = now
    application.rejection_reason = reason
    application.proof_delete_after = now + PROOF_RETENTION
    user = db.query(User).filter(User.id == application.user_id).first()
    _notification(
        db,
        application.user_id,
        "Student verification update",
        "Your student verification was not approved. Review the reason and submit a new application if appropriate.",
        NotificationType.WARNING,
        application.id,
    )
    db.commit()
    db.refresh(application)
    if user is not None:
        await EmailService().send_student_verification_email(
            user.email,
            application.applicant_name,
            "rejected",
            reason,
        )
    return _admin_application_response(db, application)
