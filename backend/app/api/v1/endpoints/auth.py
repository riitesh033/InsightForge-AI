from fastapi import HTTPException
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.db.session import get_db

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)

from app.crud.crud_user import (
    create_user,
    get_user_by_email,
    authenticate_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):

    existing_user = get_user_by_email(
        db,
        user.email
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )


    return create_user(
        db,
        user
    )


@router.get("/test")
def test():
    return {
        "message": "Auth router works!"
    }

@router.post(
    "/login",
    response_model=Token,
)
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    db_user = authenticate_user(
        db,
        user.email,
        user.password,
    )

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        subject=db_user.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }