from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.notification import NotificationType
from app.models.student_verification import (
    StudentVerificationApplication,
    StudentVerificationStatus,
)
from app.models.user import User
from app.services.email import EmailService
from app.services.entitlements import resolve_plan
from app.services.student_verification import (
    _notification,
    application_response,
    cleanup_expired_proofs,
    delete_proof,
    maybe_notify_entitlement_events,
    persist_proof,
    remove_stored_proof,
    utcnow_naive,
)

router = APIRouter()


def _latest_application(db: Session, user_id: int):
    return (
        db.query(StudentVerificationApplication)
        .filter(StudentVerificationApplication.user_id == user_id)
        .order_by(
            StudentVerificationApplication.created_at.desc(),
            StudentVerificationApplication.id.desc(),
        )
        .first()
    )


@router.get("/me")
def get_my_student_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cleanup_expired_proofs(db)
    application = _latest_application(db, current_user.id)
    maybe_notify_entitlement_events(db, current_user.id, application)
    plan_key, _ = resolve_plan(db, current_user.id)
    active = bool(
        application
        and application.status == StudentVerificationStatus.APPROVED
        and application.student_entitlement_expires_at
        and application.student_entitlement_expires_at > utcnow_naive()
    )
    return {
        "application": application_response(application) if application else None,
        "student_access_active": active,
        "effective_plan": plan_key,
        "student_access_expires_at": (
            application.student_entitlement_expires_at.isoformat()
            if active and application and application.student_entitlement_expires_at
            else None
        ),
    }


@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def submit_student_application(
    applicant_name: str = Form(..., min_length=1, max_length=100),
    institution_name: str = Form(..., min_length=1, max_length=200),
    enrollment_number: str = Form(..., min_length=1, max_length=100),
    course_or_program: str = Form(..., min_length=1, max_length=200),
    academic_year: str = Form(..., min_length=1, max_length=50),
    graduation_year: int = Form(..., ge=1900, le=2200),
    institution_email: str | None = Form(None, max_length=255),
    additional_information: str | None = Form(None, max_length=1000),
    proof_document: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .with_for_update()
        .first()
    )
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")
    if not applicant_name.strip() or not institution_name.strip():
        raise HTTPException(status_code=422, detail="Required fields cannot be blank.")
    if not enrollment_number.strip() or not course_or_program.strip():
        raise HTTPException(status_code=422, detail="Required fields cannot be blank.")
    if not academic_year.strip():
        raise HTTPException(status_code=422, detail="Required fields cannot be blank.")
    if institution_email and (
        "@" not in institution_email
        or len(institution_email) > 255
        or any(character.isspace() for character in institution_email)
    ):
        raise HTTPException(status_code=422, detail="Enter a valid institution email.")

    cleanup_expired_proofs(db)
    existing = (
        db.query(StudentVerificationApplication)
        .filter(StudentVerificationApplication.user_id == user.id)
        .with_for_update()
        .all()
    )
    if any(
        application.status == StudentVerificationStatus.PENDING
        for application in existing
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending student verification application.",
        )
    if any(
        application.status == StudentVerificationStatus.APPROVED
        and application.student_entitlement_expires_at
        and application.student_entitlement_expires_at > utcnow_naive()
        for application in existing
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your student Pro access is already active.",
        )

    original_name, stored_name, proof_size, proof_type = await persist_proof(
        proof_document
    )
    application = StudentVerificationApplication(
        user_id=user.id,
        applicant_name=applicant_name.strip(),
        institution_name=institution_name.strip(),
        enrollment_number=enrollment_number.strip(),
        course_or_program=course_or_program.strip(),
        academic_year=academic_year.strip(),
        graduation_year=graduation_year,
        institution_email=institution_email.strip() if institution_email else None,
        additional_information=(
            additional_information.strip() if additional_information else None
        ),
        proof_original_filename=original_name,
        proof_stored_filename=stored_name,
        proof_content_type=proof_type,
        proof_size=proof_size,
        status=StudentVerificationStatus.PENDING,
    )
    db.add(application)
    try:
        db.flush()
        _notification(
            db,
            user.id,
            "Student verification submitted",
            "Your student verification application is awaiting admin review.",
            NotificationType.INFO,
            application.id,
        )
        db.commit()
        db.refresh(application)
    except IntegrityError as error:
        db.rollback()
        remove_stored_proof(stored_name)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending application already exists.",
        ) from error
    return application_response(application)


@router.post("/applications/{application_id}/withdraw")
def withdraw_student_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = (
        db.query(StudentVerificationApplication)
        .filter(
            StudentVerificationApplication.id == application_id,
            StudentVerificationApplication.user_id == current_user.id,
        )
        .with_for_update()
        .first()
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    if application.status != StudentVerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending applications can be withdrawn.",
        )
    delete_proof(application)
    application.status = StudentVerificationStatus.WITHDRAWN
    application.proof_delete_after = utcnow_naive()
    db.commit()
    db.refresh(application)
    return application_response(application)
