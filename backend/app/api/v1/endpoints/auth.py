from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.crud_user import (
    authenticate_user,
    create_user,
    get_user_by_email,
)
from app.db.session import get_db
from app.schemas.user import (
    ForgotPasswordRequest,
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
    user = get_user_by_email(
        db=db,
        email=request.email,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Email sending will be added later.
    return {
        "message": "Password reset link sent successfully."
    }


# ==========================
# Test Route
# ==========================

@router.get("/test")
def test():
    return {
        "message": "Authentication API is working."
    }