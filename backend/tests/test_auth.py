"""PHASE 4/5/6 — Authentication, password management and reset flow tests."""

import asyncio
from http.cookies import SimpleCookie
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    verify_password,
)
from app.models.user import User
from app.services.email import EmailService, build_password_reset_url

API = "/api/v1"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    def test_registration_attempts_welcome_email(
        self,
        client,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        sent = []

        async def fake_send(to_email, user_name):
            sent.append((to_email, user_name))
            return True

        monkeypatch.setattr(
            auth_module.email_service,
            "send_registration_email",
            fake_send,
        )

        response = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "New User",
                "email": "new-user@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 201
        assert sent == [("new-user@example.com", "New User")]

    def test_registration_sends_welcome_email_after_database_commit(
        self,
        client,
        db,
        monkeypatch,
    ):
        """
        The current implementation sends the welcome email synchronously
        after db.commit(). This test verifies that registration succeeds and
        the email is attempted after the database transaction is committed.
        """
        from app.api.v1.endpoints import auth as auth_module
        from app.schemas.user import UserCreate

        events = []

        original_commit = db.commit

        def tracked_commit():
            original_commit()
            events.append("commit")

        async def fake_send(to_email, user_name):
            events.append(("email", to_email, user_name))
            return True

        monkeypatch.setattr(db, "commit", tracked_commit)
        monkeypatch.setattr(
            auth_module.email_service,
            "send_registration_email",
            fake_send,
        )

        created_user = asyncio.run(
            auth_module.register(
                UserCreate(
                    full_name="Queued User",
                    email="queued-user@example.com",
                    password="Password123",
                ),
                db,
            )
        )

        assert created_user.email == "queued-user@example.com"
        assert "commit" in events
        assert events[-1] == (
            "email",
            "queued-user@example.com",
            "Queued User",
        )

    def test_email_failure_does_not_fail_registration_or_leak_error(
        self,
        client,
        monkeypatch,
        caplog,
    ):
        from app.api.v1.endpoints import auth as auth_module

        sensitive_error = "test-only-provider-error"

        async def failed_send(to_email, user_name):
            raise OSError(sensitive_error)

        monkeypatch.setattr(
            auth_module.email_service,
            "send_registration_email",
            failed_send,
        )

        response = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Email Failure",
                "email": "email-failure@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == "email-failure@example.com"
        assert sensitive_error not in caplog.text

    def test_unconfigured_email_does_not_block_registration(
        self,
        client,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        async def not_configured(to_email, user_name):
            return False

        monkeypatch.setattr(
            auth_module.email_service,
            "send_registration_email",
            not_configured,
        )

        response = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Email Not Configured",
                "email": "email-not-configured@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == "email-not-configured@example.com"

    def test_successful_registration(self, client):
        r = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Bob New",
                "email": "bob@example.com",
                "password": "Password123",
            },
        )

        assert r.status_code == 201

        body = r.json()
        assert body["email"] == "bob@example.com"
        assert body["is_active"] is True

        # Sensitive fields must never be returned.
        assert "password" not in body
        assert "hashed_password" not in body

    def test_duplicate_email_rejected(self, client, user_dict):
        r = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Fake Alice",
                "email": user_dict["email"],
                "password": "Password123",
            },
        )

        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_invalid_email_rejected(self, client):
        r = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Bad Email",
                "email": "not-an-email",
                "password": "Password123",
            },
        )

        assert r.status_code == 422

    def test_short_password_rejected(self, client):
        r = client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Weak Pass",
                "email": "weak@example.com",
                "password": "short",
            },
        )

        assert r.status_code == 422

    def test_missing_fields_rejected(self, client):
        r = client.post(
            f"{API}/auth/register",
            json={"email": "x@example.com"},
        )

        assert r.status_code == 422

    def test_password_hashed_in_database(self, client, db):
        client.post(
            f"{API}/auth/register",
            json={
                "full_name": "Hash Check",
                "email": "hash@example.com",
                "password": "PlainSecret99",
            },
        )

        user = (
            db.query(User)
            .filter(User.email == "hash@example.com")
            .first()
        )

        assert user is not None
        assert user.hashed_password != "PlainSecret99"
        assert user.hashed_password.startswith("$2")
        assert verify_password("PlainSecret99", user.hashed_password)


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

class TestGoogleOAuth:
    def test_login_sets_secure_cross_site_cookies_at_callback_path(
        self,
        client,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        callback_url = (
            "https://insightforge-ai-backend-85vm.onrender.com"
            "/api/v1/auth/google/callback"
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_ID",
            "test-client-id",
        )
        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_SECRET",
            "test-client-secret",
        )
        monkeypatch.setattr(
            settings,
            "GOOGLE_CALLBACK_URL",
            callback_url,
        )
        monkeypatch.setattr(
            settings,
            "ENVIRONMENT",
            "development",
        )

        response = client.get(f"{API}/auth/google/login")

        assert response.status_code == 200

        set_cookie_headers = response.headers.get_list("set-cookie")

        assert len(set_cookie_headers) == 2

        for cookie_name in (
            "google_oauth_state",
            "google_oauth_nonce",
        ):
            header = next(
                value
                for value in set_cookie_headers
                if value.startswith(f"{cookie_name}=")
            )

            cookie = SimpleCookie()
            cookie.load(header)

            morsel = cookie[cookie_name]

            assert morsel["httponly"]
            assert morsel["secure"]
            assert morsel["samesite"].lower() == "none"
            assert morsel["path"] == "/api/v1/auth/google/callback"

    def test_callback_rejects_missing_state_cookie(
        self,
        client,
        monkeypatch,
    ):
        frontend_url = "https://frontend.example.test"

        monkeypatch.setattr(
            settings,
            "FRONTEND_URL",
            frontend_url,
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CALLBACK_URL",
            "https://backend.example.test/api/v1/auth/google/callback",
        )

        response = client.get(
            f"{API}/auth/google/callback",
            params={
                "code": "test-code",
                "state": "test-state",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        assert response.headers["location"] == (
            f"{frontend_url}/login?google_error=invalid_state"
        )

        assert "google_oauth_state=" in response.headers.get(
            "set-cookie",
            "",
        )

    def test_callback_rejects_mismatched_state(
        self,
        client,
        monkeypatch,
    ):
        frontend_url = "https://frontend.example.test"

        monkeypatch.setattr(
            settings,
            "FRONTEND_URL",
            frontend_url,
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CALLBACK_URL",
            "https://backend.example.test/api/v1/auth/google/callback",
        )

        response = client.get(
            f"{API}/auth/google/callback",
            params={
                "code": "test-code",
                "state": "state-from-google",
            },
            cookies={
                "google_oauth_state": "different-state",
                "google_oauth_nonce": "test-nonce",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        assert response.headers["location"] == (
            f"{frontend_url}/login?google_error=invalid_state"
        )

    def test_callback_rejects_invalid_nonce_without_logging_secrets(
        self,
        client,
        monkeypatch,
        caplog,
    ):
        from google.oauth2 import id_token
        from app.api.v1.endpoints import auth as auth_module

        frontend_url = "https://frontend.example.test"

        monkeypatch.setattr(
            settings,
            "FRONTEND_URL",
            frontend_url,
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_ID",
            "test-client-id",
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_SECRET",
            "test-client-secret",
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CALLBACK_URL",
            "https://backend.example.test/api/v1/auth/google/callback",
        )

        class FakeTokenResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "id_token": "sensitive-google-id-token",
                }

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, data):
                return FakeTokenResponse()

        monkeypatch.setattr(
            auth_module.httpx,
            "AsyncClient",
            FakeAsyncClient,
        )

        monkeypatch.setattr(
            id_token,
            "verify_oauth2_token",
            lambda token, request, audience: {
                "nonce": "nonce-from-different-login",
                "email": "google-user@example.com",
                "sub": "google-subject-id",
                "email_verified": True,
            },
        )

        response = client.get(
            f"{API}/auth/google/callback",
            params={
                "code": "sensitive-authorization-code",
                "state": "valid-state",
            },
            cookies={
                "google_oauth_state": "valid-state",
                "google_oauth_nonce": "expected-nonce",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        assert response.headers["location"] == (
            f"{frontend_url}/login?google_error=invalid_state"
        )

        for secret in (
            "sensitive-google-id-token",
            "sensitive-authorization-code",
            "expected-nonce",
            "nonce-from-different-login",
        ):
            assert secret not in caplog.text

    def test_new_user_and_repeat_login_authenticate_without_duplicate_email(
        self,
        client,
        db,
        monkeypatch,
        caplog,
    ):
        from google.oauth2 import id_token
        from app.api.v1.endpoints import auth as auth_module

        callback_url = (
            "https://insightforge-ai-backend-85vm.onrender.com"
            "/api/v1/auth/google/callback"
        )

        frontend_url = (
            "https://insightforge-ai-72pf.onrender.com"
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_ID",
            "test-client-id",
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CLIENT_SECRET",
            "test-client-secret",
        )

        monkeypatch.setattr(
            settings,
            "GOOGLE_CALLBACK_URL",
            callback_url,
        )

        monkeypatch.setattr(
            settings,
            "FRONTEND_URL",
            frontend_url,
        )

        expected_nonce = ""
        exchanged_code = []
        welcome_emails = []

        class FakeTokenResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "id_token": "test-google-id-token",
                }

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, data):
                assert url == "https://oauth2.googleapis.com/token"
                assert data["redirect_uri"] == callback_url

                exchanged_code.append(data["code"])

                return FakeTokenResponse()

        async def fake_welcome_email(to_email, user_name):
            welcome_emails.append(
                (to_email, user_name)
            )
            return True

        monkeypatch.setattr(
            auth_module.httpx,
            "AsyncClient",
            FakeAsyncClient,
        )

        monkeypatch.setattr(
            id_token,
            "verify_oauth2_token",
            lambda token, request, audience: {
                "nonce": expected_nonce,
                "email": "google-user@example.com",
                "sub": "google-subject-id",
                "email_verified": True,
                "name": "Google User",
                "picture": "https://example.test/avatar.png",
            },
        )

        monkeypatch.setattr(
            auth_module.email_service,
            "send_registration_email",
            fake_welcome_email,
        )

        def authorize_and_return():
            nonlocal expected_nonce

            authorization = client.get(
                f"{API}/auth/google/login"
            )

            assert authorization.status_code == 200

            authorization_params = parse_qs(
                urlsplit(
                    authorization.json()["authorization_url"]
                ).query
            )

            expected_nonce = authorization_params["nonce"][0]

            assert authorization_params["redirect_uri"] == [
                callback_url
            ]

            cookie_values = {}

            for cookie_header in authorization.headers.get_list(
                "set-cookie"
            ):
                cookie = SimpleCookie()
                cookie.load(cookie_header)

                cookie_values.update({
                    name: morsel.value
                    for name, morsel in cookie.items()
                })

            callback = client.get(
                f"{API}/auth/google/callback",
                params={
                    "code": f"test-code-{len(exchanged_code)}",
                    "state": authorization_params["state"][0],
                },
                cookies=cookie_values,
                follow_redirects=False,
            )

            assert callback.status_code == 303

            return urlsplit(
                callback.headers["location"]
            )

        first_redirect = authorize_and_return()

        assert first_redirect.scheme == "https"
        assert (
            first_redirect.netloc
            == "insightforge-ai-72pf.onrender.com"
        )
        assert first_redirect.path == "/auth/google/callback"

        first_token = parse_qs(
            first_redirect.fragment
        )["access_token"][0]

        assert first_token

        first_user = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": f"Bearer {first_token}"
            },
        )

        assert first_user.status_code == 200
        assert first_user.json()["email"] == (
            "google-user@example.com"
        )

        first_user_id = first_user.json()["id"]

        second_redirect = authorize_and_return()

        second_token = parse_qs(
            second_redirect.fragment
        )["access_token"][0]

        second_user = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": f"Bearer {second_token}"
            },
        )

        assert second_user.status_code == 200
        assert second_user.json()["id"] == first_user_id

        assert db.query(User).filter(
            User.email == "google-user@example.com"
        ).count() == 1

        assert exchanged_code == [
            "test-code-0",
            "test-code-1",
        ]

        assert welcome_emails == [
            (
                "google-user@example.com",
                "Google User",
            )
        ]

        for sensitive_value in (
            "test-client-secret",
            "test-google-id-token",
            "test-code-0",
            "test-code-1",
            expected_nonce,
            first_token,
            second_token,
        ):
            assert sensitive_value not in caplog.text


# ---------------------------------------------------------------------------
# Brevo HTTPS Email Service
# ---------------------------------------------------------------------------

class TestRegistrationEmailService:
    def test_uses_brevo_api_and_verified_sender(
        self,
        monkeypatch,
    ):
        from app.services import email as email_module

        monkeypatch.setattr(
            settings,
            "BREVO_API_KEY",
            "test-brevo-api-key",
        )

        monkeypatch.setattr(
            settings,
            "SMTP_FROM_EMAIL",
            "verified-sender@example.test",
        )

        monkeypatch.setattr(
            settings,
            "SMTP_FROM_NAME",
            "InsightForge Test",
        )

        captured = {}

        class FakeResponse:
            status_code = 201

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                captured["timeout"] = kwargs.get("timeout")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(
                self,
                url,
                headers,
                json,
            ):
                captured["url"] = url
                captured["headers"] = headers
                captured["json"] = json

                return FakeResponse()

        monkeypatch.setattr(
            email_module.httpx,
            "AsyncClient",
            FakeAsyncClient,
        )

        service = EmailService()

        delivered = asyncio.run(
            service.send_registration_email(
                "new-user@example.test",
                "New User",
            )
        )

        assert delivered is True

        assert captured["url"] == (
            "https://api.brevo.com/v3/smtp/email"
        )

        assert captured["headers"]["accept"] == (
            "application/json"
        )

        assert captured["headers"]["content-type"] == (
            "application/json"
        )

        assert captured["headers"]["api-key"] == (
            "test-brevo-api-key"
        )

        assert captured["json"]["sender"] == {
            "name": "InsightForge Test",
            "email": "verified-sender@example.test",
        }

        assert captured["json"]["to"] == [
            {
                "email": "new-user@example.test",
            }
        ]

        assert captured["json"]["subject"]
        assert captured["json"]["htmlContent"]

    def test_unconfigured_brevo_returns_false_without_secret_values(
        self,
        monkeypatch,
        caplog,
    ):
        monkeypatch.setattr(
            settings,
            "BREVO_API_KEY",
            "",
        )

        monkeypatch.setattr(
            settings,
            "SMTP_FROM_EMAIL",
            "",
        )

        delivered = asyncio.run(
            EmailService().send_registration_email(
                "new-user@example.test",
                "New User",
            )
        )

        assert delivered is False

        assert "BREVO_API_KEY" in caplog.text
        assert "SMTP_FROM_EMAIL" in caplog.text

        assert "test-brevo-api-key" not in caplog.text
        assert "test-smtp-password" not in caplog.text


# ---------------------------------------------------------------------------
# Login / JWT
# ---------------------------------------------------------------------------

class TestLogin:
    def test_valid_credentials_return_jwt(
        self,
        client,
        user_dict,
    ):
        r = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": user_dict["password"],
            },
        )

        assert r.status_code == 200

        body = r.json()

        assert body["token_type"] == "bearer"

        payload = jwt.decode(
            body["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        assert payload["sub"] == user_dict["email"]
        assert "exp" in payload

    def test_wrong_password_401(
        self,
        client,
        user_dict,
    ):
        r = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": "WrongPassword!",
            },
        )

        assert r.status_code == 401

    def test_nonexistent_user_401(self, client):
        r = client.post(
            f"{API}/auth/login",
            data={
                "username": "ghost@example.com",
                "password": "Whatever123",
            },
        )

        assert r.status_code == 401

    def test_expired_token_rejected(
        self,
        client,
        user_dict,
    ):
        expired = jwt.encode(
            {
                "sub": user_dict["email"],
                "exp": datetime.now(UTC) - timedelta(minutes=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        r = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": f"Bearer {expired}"
            },
        )

        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Current user / protected routes
# ---------------------------------------------------------------------------

class TestCurrentUser:
    def test_me_with_valid_token(
        self,
        client,
        user_dict,
        auth_headers,
    ):
        r = client.get(
            f"{API}/users/me",
            headers=auth_headers,
        )

        assert r.status_code == 200

        body = r.json()

        assert body["email"] == user_dict["email"]
        assert "hashed_password" not in body
        assert "password" not in body

    def test_me_without_token_401(self, client):
        assert client.get(
            f"{API}/users/me"
        ).status_code == 401

    def test_me_malformed_token_401(self, client):
        r = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": "Bearer garbage.token.here"
            },
        )

        assert r.status_code == 401

    def test_me_token_for_deleted_user_401(
        self,
        client,
    ):
        token = create_access_token(
            subject="deleted@example.com"
        )

        r = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert r.status_code == 401

    def test_me_token_for_inactive_user_401(
        self,
        client,
        user_dict,
        auth_headers,
        db,
    ):
        user = (
            db.query(User)
            .filter(User.email == user_dict["email"])
            .one()
        )

        user.is_active = False
        db.commit()

        response = client.get(
            f"{API}/users/me",
            headers=auth_headers,
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Could not validate credentials"
        )

    def test_protected_dataset_route_requires_auth(
        self,
        client,
    ):
        r = client.get(
            f"{API}/datasets/"
        )

        assert r.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(
        self,
        client,
        user_dict,
    ):
        forged = jwt.encode(
            {
                "sub": user_dict["email"],
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "attacker-secret",
            algorithm=settings.ALGORITHM,
        )

        r = client.get(
            f"{API}/users/me",
            headers={
                "Authorization": f"Bearer {forged}"
            },
        )

        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_flow(
        self,
        client,
        user_dict,
        auth_headers,
    ):
        r = client.post(
            f"{API}/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": user_dict["password"],
                "new_password": "BrandNewPass456",
            },
        )

        assert r.status_code == 200

        r = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": user_dict["password"],
            },
        )

        assert r.status_code == 401

        r = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": "BrandNewPass456",
            },
        )

        assert r.status_code == 200

    def test_wrong_current_password_fails(
        self,
        client,
        auth_headers,
    ):
        r = client.post(
            f"{API}/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "NotThePassword1",
                "new_password": "BrandNewPass456",
            },
        )

        assert r.status_code == 400

    def test_weak_new_password_rejected(
        self,
        client,
        auth_headers,
        user_dict,
    ):
        r = client.post(
            f"{API}/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": user_dict["password"],
                "new_password": "abc",
            },
        )

        assert r.status_code == 422

    def test_change_password_requires_auth(
        self,
        client,
    ):
        r = client.post(
            f"{API}/users/me/change-password",
            json={
                "current_password": "whatever123",
                "new_password": "another456",
            },
        )

        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    def test_reset_url_encodes_token_and_trims_frontend_slash(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            settings,
            "FRONTEND_URL",
            "https://frontend.example.test/",
        )

        reset_url = build_password_reset_url(
            "token+with/slash="
        )

        parsed_url = urlsplit(reset_url)

        assert parsed_url.path == "/reset-password"

        assert parsed_url.query == (
            "token=token%2Bwith%2Fslash%3D"
        )

        assert parse_qs(parsed_url.query)["token"] == [
            "token+with/slash="
        ]

    def test_known_email_sends_email_with_token_url(
        self,
        client,
        user_dict,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        sent = {}

        async def fake_send(
            to_email,
            reset_url,
        ):
            sent["to_email"] = to_email
            sent["reset_url"] = reset_url

        monkeypatch.setattr(
            auth_module.email_service,
            "send_password_reset_email",
            fake_send,
        )

        monkeypatch.setattr(
            auth_module.settings,
            "FRONTEND_URL",
            "https://frontend.example.test/",
        )

        r = client.post(
            f"{API}/auth/forgot-password",
            json={
                "email": user_dict["email"]
            },
        )

        assert r.status_code == 200

        assert r.json()["message"] == (
            "If the account exists, a password reset email has been sent."
        )

        assert sent["to_email"] == user_dict["email"]

        parsed_url = urlsplit(
            sent["reset_url"]
        )

        assert parsed_url.scheme == urlsplit(
            settings.FRONTEND_URL
        ).scheme

        assert parsed_url.netloc == urlsplit(
            settings.FRONTEND_URL
        ).netloc

        assert parsed_url.path == "/reset-password"

        assert set(
            parse_qs(parsed_url.query)
        ) == {"token"}

        token = parse_qs(
            parsed_url.query
        )["token"][0]

        payload = decode_password_reset_token(token)

        assert payload is not None
        assert payload["sub"] == user_dict["email"]
        assert payload["type"] == "password_reset"

        reset_response = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": token,
                "new_password": "RoundTripPass789",
            },
        )

        assert reset_response.status_code == 200

        login_response = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": "RoundTripPass789",
            },
        )

        assert login_response.status_code == 200

        assert user_dict["password"] not in sent[
            "reset_url"
        ]

    def test_unknown_email_no_enumeration_no_email(
        self,
        client,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        calls = []

        async def fake_send(
            to_email,
            reset_url,
        ):
            calls.append(to_email)

        monkeypatch.setattr(
            auth_module.email_service,
            "send_password_reset_email",
            fake_send,
        )

        known = client.post(
            f"{API}/auth/forgot-password",
            json={
                "email": "nobody@example.com"
            },
        )

        assert known.status_code == 200

        assert known.json()["message"] == (
            "If the account exists, a password reset email has been sent."
        )

        assert "reset_token" not in known.json()

        assert calls == []

    def test_email_failure_does_not_break_endpoint(
        self,
        client,
        user_dict,
        monkeypatch,
    ):
        from app.api.v1.endpoints import auth as auth_module

        async def broken_send(
            to_email,
            reset_url,
        ):
            raise OSError("email provider unavailable")

        monkeypatch.setattr(
            auth_module.email_service,
            "send_password_reset_email",
            broken_send,
        )

        r = client.post(
            f"{API}/auth/forgot-password",
            json={
                "email": user_dict["email"]
            },
        )

        assert r.status_code == 200

    def test_reset_token_expiry_and_type_binding(self):
        token = create_password_reset_token(
            "someone@example.com"
        )

        payload = decode_password_reset_token(token)

        exp = datetime.fromtimestamp(
            payload["exp"],
            tz=UTC,
        )

        remaining = (
            exp - datetime.now(UTC)
        ).total_seconds()

        assert 3500 < remaining <= 3600

        access = create_access_token(
            "someone@example.com"
        )

        assert decode_password_reset_token(
            access
        ) is None


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_valid_token_resets_password(
        self,
        client,
        user_dict,
    ):
        token = create_password_reset_token(
            user_dict["email"]
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": token,
                "new_password": "FreshPassword789",
            },
        )

        assert r.status_code == 200

        old = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": user_dict["password"],
            },
        )

        assert old.status_code == 401

        new = client.post(
            f"{API}/auth/login",
            data={
                "username": user_dict["email"],
                "password": "FreshPassword789",
            },
        )

        assert new.status_code == 200

    def test_invalid_signature_rejected(
        self,
        client,
        user_dict,
    ):
        forged = jwt.encode(
            {
                "sub": user_dict["email"],
                "type": "password_reset",
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "wrong-secret",
            algorithm=settings.ALGORITHM,
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": forged,
                "new_password": "HackedPassword1",
            },
        )

        assert r.status_code == 400

    def test_expired_token_rejected(
        self,
        client,
        user_dict,
    ):
        expired = jwt.encode(
            {
                "sub": user_dict["email"],
                "type": "password_reset",
                "exp": datetime.now(UTC) - timedelta(minutes=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": expired,
                "new_password": "TooLatePass123",
            },
        )

        assert r.status_code == 400

    def test_malformed_token_rejected(self, client):
        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": "!!!not-a-jwt!!!",
                "new_password": "Anything1234",
            },
        )

        assert r.status_code == 400

    def test_access_token_cannot_reset_password(
        self,
        client,
        user_dict,
    ):
        access = create_access_token(
            user_dict["email"]
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": access,
                "new_password": "SneakyPassword1",
            },
        )

        assert r.status_code == 400

    def test_weak_new_password_rejected(
        self,
        client,
        user_dict,
    ):
        token = create_password_reset_token(
            user_dict["email"]
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": token,
                "new_password": "short",
            },
        )

        assert r.status_code == 422

    def test_token_for_nonexistent_user_rejected(
        self,
        client,
    ):
        token = create_password_reset_token(
            "gone@example.com"
        )

        r = client.post(
            f"{API}/auth/reset-password",
            json={
                "token": token,
                "new_password": "Whatever1234",
            },
        )

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Full end-to-end authentication journey
# ---------------------------------------------------------------------------

def test_end_to_end_auth_journey(
    client,
    monkeypatch,
):
    from app.api.v1.endpoints import auth as auth_module

    captured = {}

    async def fake_send(
        to_email,
        reset_url,
    ):
        captured["url"] = reset_url

    monkeypatch.setattr(
        auth_module.email_service,
        "send_password_reset_email",
        fake_send,
    )

    # 1. Register
    creds = {
        "full_name": "E2E User",
        "email": "e2e@example.com",
        "password": "FirstPass123",
    }

    assert client.post(
        f"{API}/auth/register",
        json=creds,
    ).status_code == 201

    # 2. Login
    login = client.post(
        f"{API}/auth/login",
        data={
            "username": creds["email"],
            "password": creds["password"],
        },
    )

    assert login.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    # 3. Current user
    me = client.get(
        f"{API}/users/me",
        headers=headers,
    )

    assert (
        me.status_code == 200
        and me.json()["email"] == creds["email"]
    )

    # 4. Change password
    cp = client.post(
        f"{API}/users/me/change-password",
        headers=headers,
        json={
            "current_password": creds["password"],
            "new_password": "SecondPass456",
        },
    )

    assert cp.status_code == 200

    # 5. Re-login with new password
    relogin = client.post(
        f"{API}/auth/login",
        data={
            "username": creds["email"],
            "password": "SecondPass456",
        },
    )

    assert relogin.status_code == 200

    # 6. Logout behavior (stateless JWT):
    # without the client token, protected calls fail again.
    anon = client.get(
        f"{API}/users/me"
    )

    assert anon.status_code == 401

    # 7. Forgot password -> capture reset email
    fp = client.post(
        f"{API}/auth/forgot-password",
        json={
            "email": creds["email"]
        },
    )

    assert fp.status_code == 200
    assert "url" in captured

    # 8. Reset through emailed link's token
    reset_token = captured["url"].split(
        "token=",
        1,
    )[1]

    rp = client.post(
        f"{API}/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "ThirdPass789",
        },
    )

    assert rp.status_code == 200

    # 9. Final login with reset password;
    # previous password is dead.
    final = client.post(
        f"{API}/auth/login",
        data={
            "username": creds["email"],
            "password": "ThirdPass789",
        },
    )

    assert final.status_code == 200

    stale = client.post(
        f"{API}/auth/login",
        data={
            "username": creds["email"],
            "password": "SecondPass456",
        },
    )

    assert stale.status_code == 401