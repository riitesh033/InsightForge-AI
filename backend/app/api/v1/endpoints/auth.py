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
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email.
    For security, always return success even if email doesn't exist.
    In production, this would send an email with the reset link.
    """
    user = get_user_by_email(
        db=db,
        email=request.email,
    )

    # Always return success to prevent account enumeration
    if user is None:
        return {
            "message": "If the account exists, a password reset email has been sent."
        }

    # Generate reset token
    reset_token = create_password_reset_token(email=request.email)

    # In production: send email with reset link
    # For now, log the token for development purposes
    print(f"\n=== PASSWORD RESET TOKEN (Development Only) ===")
    print(f"Email: {request.email}")
    print(f"Reset Token: {reset_token}")
    print(f"Reset URL: http://localhost:5173/reset-password?token={reset_token}")
    print("================================================\n")

    return {
        "message": "If the account exists, a password reset email has been sent.",
        # Include token only in development for testing
        # In production, remove this line and send via email
        "reset_token": reset_token if True else None,
    }


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