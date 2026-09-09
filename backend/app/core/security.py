from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(subject: str) -> str:
    """
    Generate a JWT access token.
    """
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any] | None:
    """
    Decode and verify a JWT token.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token for an email address.
    Token expires in 1 hour.
    """
    expire = datetime.now(UTC) + timedelta(hours=1)
    
    payload = {
        "sub": email,
        "type": "password_reset",
        "exp": expire,
    }
    
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_password_reset_token(
    token: str,
) -> dict[str, Any] | None:
    """
    Decode and verify a password reset token.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Verify this is actually a password reset token
        if payload.get("type") != "password_reset":
            return None
            
        return payload
        
    except JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.
    Token expires in 24 hours.
    """
    expire = datetime.now(UTC) + timedelta(hours=24)
    
    payload = {
        "sub": email,
        "type": "email_verification",
        "exp": expire,
    }
    
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_email_verification_token(
    token: str,
) -> dict[str, Any] | None:
    """
    Decode and verify an email verification token.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Verify this is actually an email verification token
        if payload.get("type") != "email_verification":
            return None
            
        return payload
        
    except JWTError:
        return None