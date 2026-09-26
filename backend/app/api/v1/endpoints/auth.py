import logging

from app.core.config import settings
from app.services.email import email_service

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
)
from app.crud.crud_user import (
    authenticate_user,
    create_user,
    get_user_by_email,
    update_password,
)
from app.db.session import get_db
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
)

router = APIRouter()


# ==========================
# Register
# ==========================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(
        db=db,
        email=user.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    return create_user(
        db=db,
        user=user,
    )


# ==========================
# Login
# ==========================

@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        subject=user.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ==========================
# Forgot Password
# ==========================

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email.
    For security, always return success even if email doesn't exist.
    In production, this would send an email with the reset link.
    """
    generic_message = (
        "If the account exists, a password reset email has been sent."
    )

    user = get_user_by_email(
        db=db,
        email=request.email,
    )

    # Unknown email: return the SAME externally visible response so that
    # account existence is never revealed, and send no email.
    if user is None:
        return {"message": generic_message}

    # Generate a signed, single-purpose reset token (1 hour expiry).
    reset_token = create_password_reset_token(email=request.email)

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # Send the reset email through the email service. The service itself
    # decides whether SMTP is configured; failures are logged server-side
    # only and never leaked to the client.
    try:
        await email_service.send_password_reset_email(
            to_email=request.email,
            reset_url=reset_url,
        )
    except Exception:
        logger.exception("Failed to deliver password reset email")

    response: dict = {"message": generic_message}

    # Development-only convenience so the flow is testable without SMTP.
    # NEVER exposed in production (tokens must not appear in responses there).
    if not settings.is_production:
        logger.info("Password reset requested for development account.")
        response["reset_token"] = reset_token

    return response


# ==========================
# Reset Password
# ==========================

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset password using a valid reset token.
    """
    # Decode and validate token
    payload = decode_password_reset_token(request.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token.",
        )

    # Get user by email from token
    user = get_user_by_email(
        db=db,
        email=email,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Update password
    update_password(
        db=db,
        user=user,
        new_password=request.new_password,
    )

    return {
        "message": "Password has been reset successfully.",
    }


# ==========================
# Test Route
# ==========================

@router.get("/test")
def test():
    return {
        "message": "Authentication API is working."
    }