import logging
import secrets
from urllib.parse import urlencode, urlsplit

import httpx
from app.core.config import settings
from app.services.email import build_password_reset_url, email_service

logger = logging.getLogger(__name__)

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
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
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
)

router = APIRouter()


async def _send_registration_email_safely(
    to_email: str,
    user_name: str,
) -> None:
    try:
        sent = await email_service.send_registration_email(to_email, user_name)
        if not sent:
            logger.warning("Registration welcome email was not delivered.")
    except Exception as error:
        logger.error("Registration email failed (%s)", type(error).__name__)


# ==========================
# Register
# ==========================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    background_tasks: BackgroundTasks,
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

    created = create_user(
        db=db,
        user=user,
    )
    db.add(Notification(
        user_id=created.id,
        title="Welcome to InsightForge AI",
        message="Your account was created successfully.",
        notification_type=NotificationType.SUCCESS,
        action_url="/dashboard",
    ))
    db.commit()
    background_tasks.add_task(
        _send_registration_email_safely,
        created.email,
        created.full_name,
    )
    return created


def _google_configuration() -> tuple[str, str, str]:
    client_id = settings.GOOGLE_CLIENT_ID.strip()
    client_secret = settings.GOOGLE_CLIENT_SECRET.strip()
    callback_url = settings.GOOGLE_CALLBACK_URL.strip()
    if not client_id or not client_secret or not callback_url:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured. Use email and password instead.",
        )
    return client_id, client_secret, callback_url


@router.get("/google/login")
def begin_google_login(response: Response) -> dict[str, str]:
    client_id, _, callback_url = _google_configuration()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    cookie_path = urlsplit(callback_url).path
    cookie_options = {
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "max_age": 600,
        "path": cookie_path,
    }
    response.set_cookie("google_oauth_state", state, **cookie_options)
    response.set_cookie("google_oauth_nonce", nonce, **cookie_options)
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "prompt": "select_account",
        }
    )
    return {"authorization_url": authorization_url}


def _google_failure(code: str) -> RedirectResponse:
    location = f"{settings.FRONTEND_URL.rstrip('/')}/login?google_error={code}"
    return RedirectResponse(location, status_code=303)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    state_cookie = request.cookies.get("google_oauth_state")
    nonce = request.cookies.get("google_oauth_nonce")
    response_cookies = (
        "google_oauth_state",
        "google_oauth_nonce",
    )

    def clear_oauth_cookies(response: Response) -> Response:
        callback_url = settings.GOOGLE_CALLBACK_URL
        path = urlsplit(callback_url).path or "/"
        for cookie_name in response_cookies:
            response.delete_cookie(
                cookie_name,
                path=path,
                secure=settings.is_production,
                httponly=True,
                samesite="lax",
            )
        return response

    if error:
        return clear_oauth_cookies(
            _google_failure("cancelled" if error == "access_denied" else "unavailable")
        )
    if not state or not state_cookie or not secrets.compare_digest(state, state_cookie):
        return clear_oauth_cookies(_google_failure("invalid_state"))
    if not code or not nonce:
        return clear_oauth_cookies(_google_failure("invalid_response"))

    try:
        client_id, client_secret, callback_url = _google_configuration()
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": callback_url,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            token_payload = token_response.json()

        google_id_token = token_payload.get("id_token")
        if not isinstance(google_id_token, str):
            raise ValueError("Google token response is missing an ID token.")

        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            google_id_token, GoogleRequest(), client_id
        )
        if claims.get("nonce") != nonce:
            return clear_oauth_cookies(_google_failure("invalid_state"))
    except HTTPException as auth_error:
        if auth_error.status_code == 503:
            return clear_oauth_cookies(_google_failure("unavailable"))
        raise
    except (httpx.HTTPError, ValueError, TypeError) as token_error:
        logger.info("Google token exchange failed (%s)", type(token_error).__name__)
        return clear_oauth_cookies(_google_failure("invalid_response"))
    except Exception as token_error:
        logger.info("Google ID token verification failed (%s)", type(token_error).__name__)
        return clear_oauth_cookies(_google_failure("invalid_response"))

    email = str(claims.get("email", "")).strip().lower()
    google_id = str(claims.get("sub", "")).strip()
    if not email or not google_id or claims.get("email_verified") is not True:
        return clear_oauth_cookies(_google_failure("invalid_response"))

    user = get_user_by_email(db, email)
    is_new = user is None
    if user is None:
        user = User(
            full_name=str(claims.get("name") or email.split("@")[0])[:100],
            email=email,
            hashed_password=None,
            google_id=google_id,
            profile_picture=claims.get("picture"),
            is_verified=True,
        )
        db.add(user)
        db.flush()
        db.add(Notification(
            user_id=user.id,
            title="Welcome to InsightForge AI",
            message="Your Google account was connected successfully.",
            notification_type=NotificationType.SUCCESS,
            action_url="/dashboard",
        ))
    elif user.google_id and user.google_id != google_id:
        return clear_oauth_cookies(_google_failure("account_conflict"))
    else:
        user.google_id = google_id
        user.is_verified = True
        if not user.profile_picture:
            user.profile_picture = claims.get("picture")
    db.commit()
    if is_new:
        try:
            sent = await email_service.send_registration_email(
                user.email,
                user.full_name,
            )
            if not sent:
                logger.warning("Google registration welcome email was not delivered.")
        except Exception as error:
            logger.error("Google registration email failed (%s)", type(error).__name__)
    access_token = create_access_token(user.email)
    callback = RedirectResponse(
        f"{settings.FRONTEND_URL.rstrip('/')}/auth/google/callback"
        f"#access_token={access_token}",
        status_code=303,
    )
    return clear_oauth_cookies(callback)


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

    # Generate a signed reset token (1 hour expiry).
    reset_token = create_password_reset_token(email=request.email)

    reset_url = build_password_reset_url(reset_token)

    # Send the reset email through the email service. The service itself
    # decides whether SMTP is configured; failures are logged server-side
    # only and never leaked to the client.
    try:
        await email_service.send_password_reset_email(
            to_email=request.email,
            reset_url=reset_url,
        )
    except Exception as error:
        logger.error(
            "Failed to deliver password reset email (%s)",
            type(error).__name__,
        )

    return {"message": generic_message}


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

    if not isinstance(email, str) or not email:
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