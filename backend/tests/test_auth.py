"""PHASE 4/5/6 — Authentication, password management and reset flow tests."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    verify_password,
)
from app.models.user import User

API = "/api/v1"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    def test_successful_registration(self, client):
        r = client.post(f"{API}/auth/register", json={
            "full_name": "Bob New",
            "email": "bob@example.com",
            "password": "Password123",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "bob@example.com"
        assert body["is_active"] is True
        # Sensitive fields must never be returned.
        assert "password" not in body
        assert "hashed_password" not in body

    def test_duplicate_email_rejected(self, client, user_dict):
        r = client.post(f"{API}/auth/register", json={
            "full_name": "Fake Alice",
            "email": user_dict["email"],
            "password": "Password123",
        })
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_invalid_email_rejected(self, client):
        r = client.post(f"{API}/auth/register", json={
            "full_name": "Bad Email",
            "email": "not-an-email",
            "password": "Password123",
        })
        assert r.status_code == 422

    def test_short_password_rejected(self, client):
        r = client.post(f"{API}/auth/register", json={
            "full_name": "Weak Pass",
            "email": "weak@example.com",
            "password": "short",
        })
        assert r.status_code == 422

    def test_missing_fields_rejected(self, client):
        r = client.post(f"{API}/auth/register", json={"email": "x@example.com"})
        assert r.status_code == 422

    def test_password_hashed_in_database(self, client, db):
        client.post(f"{API}/auth/register", json={
            "full_name": "Hash Check",
            "email": "hash@example.com",
            "password": "PlainSecret99",
        })
        user = db.query(User).filter(User.email == "hash@example.com").first()
        assert user is not None
        assert user.hashed_password != "PlainSecret99"
        assert user.hashed_password.startswith("$2")  # bcrypt
        assert verify_password("PlainSecret99", user.hashed_password)


# ---------------------------------------------------------------------------
# Login / JWT
# ---------------------------------------------------------------------------

class TestLogin:
    def test_valid_credentials_return_jwt(self, client, user_dict):
        r = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"],
            "password": user_dict["password"],
        })
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        payload = jwt.decode(
            body["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_dict["email"]
        assert "exp" in payload

    def test_wrong_password_401(self, client, user_dict):
        r = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"],
            "password": "WrongPassword!",
        })
        assert r.status_code == 401

    def test_nonexistent_user_401(self, client):
        r = client.post(f"{API}/auth/login", data={
            "username": "ghost@example.com",
            "password": "Whatever123",
        })
        assert r.status_code == 401

    def test_expired_token_rejected(self, client, user_dict):
        expired = jwt.encode(
            {
                "sub": user_dict["email"],
                "exp": datetime.now(UTC) - timedelta(minutes=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        r = client.get(
            f"{API}/users/me", headers={"Authorization": f"Bearer {expired}"}
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Current user / protected routes
# ---------------------------------------------------------------------------

class TestCurrentUser:
    def test_me_with_valid_token(self, client, user_dict, auth_headers):
        r = client.get(f"{API}/users/me", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == user_dict["email"]
        assert "hashed_password" not in body
        assert "password" not in body

    def test_me_without_token_401(self, client):
        assert client.get(f"{API}/users/me").status_code == 401

    def test_me_malformed_token_401(self, client):
        r = client.get(f"{API}/users/me", headers={"Authorization": "Bearer garbage.token.here"})
        assert r.status_code == 401

    def test_me_token_for_deleted_user_401(self, client):
        token = create_access_token(subject="deleted@example.com")
        r = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_protected_dataset_route_requires_auth(self, client):
        # An example protected resource route must reject anonymous callers.
        r = client.get(f"{API}/datasets/")
        assert r.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(self, client, user_dict):
        forged = jwt.encode(
            {"sub": user_dict["email"], "exp": datetime.now(UTC) + timedelta(hours=1)},
            "attacker-secret",
            algorithm=settings.ALGORITHM,
        )
        r = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_flow(self, client, user_dict, auth_headers):
        r = client.post(f"{API}/users/me/change-password", headers=auth_headers, json={
            "current_password": user_dict["password"],
            "new_password": "BrandNewPass456",
        })
        assert r.status_code == 200

        # Old password rejected.
        r = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"], "password": user_dict["password"]})
        assert r.status_code == 401

        # New password accepted.
        r = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"], "password": "BrandNewPass456"})
        assert r.status_code == 200

    def test_wrong_current_password_fails(self, client, auth_headers):
        r = client.post(f"{API}/users/me/change-password", headers=auth_headers, json={
            "current_password": "NotThePassword1",
            "new_password": "BrandNewPass456",
        })
        assert r.status_code == 400

    def test_weak_new_password_rejected(self, client, auth_headers, user_dict):
        r = client.post(f"{API}/users/me/change-password", headers=auth_headers, json={
            "current_password": user_dict["password"],
            "new_password": "abc",
        })
        assert r.status_code == 422

    def test_change_password_requires_auth(self, client):
        r = client.post(f"{API}/users/me/change-password", json={
            "current_password": "whatever123", "new_password": "another456"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Forgot password (with mocked SMTP layer)
# ---------------------------------------------------------------------------

class TestForgotPassword:
    def test_known_email_sends_email_with_token_url(self, client, user_dict, monkeypatch):
        from app.api.v1.endpoints import auth as auth_module

        sent = {}

        async def fake_send(to_email, reset_url):
            sent["to_email"] = to_email
            sent["reset_url"] = reset_url

        monkeypatch.setattr(
            auth_module.email_service, "send_password_reset_email", fake_send
        )

        r = client.post(f"{API}/auth/forgot-password", json={"email": user_dict["email"]})
        assert r.status_code == 200
        assert r.json()["message"] == (
            "If the account exists, a password reset email has been sent."
        )

        # Email service invoked with correct recipient.
        assert sent["to_email"] == user_dict["email"]
        # Reset URL points at the real frontend route and carries a valid token.
        assert sent["reset_url"].startswith(f"{settings.FRONTEND_URL}/reset-password?token=")
        token = sent["reset_url"].split("token=", 1)[1]
        payload = decode_password_reset_token(token)
        assert payload is not None
        assert payload["sub"] == user_dict["email"]
        assert payload["type"] == "password_reset"
        # Raw password never appears in the email URL.
        assert user_dict["password"] not in sent["reset_url"]

    def test_unknown_email_no_enumeration_no_email(self, client, monkeypatch):
        from app.api.v1.endpoints import auth as auth_module

        calls = []

        async def fake_send(to_email, reset_url):
            calls.append(to_email)

        monkeypatch.setattr(
            auth_module.email_service, "send_password_reset_email", fake_send
        )

        known = client.post(f"{API}/auth/forgot-password", json={"email": "nobody@example.com"})
        assert known.status_code == 200
        # Identical externally visible response message.
        assert known.json()["message"] == (
            "If the account exists, a password reset email has been sent."
        )
        assert "reset_token" not in known.json()
        assert calls == []  # no email attempted for unknown account

    def test_smtp_failure_does_not_break_endpoint(self, client, user_dict, monkeypatch):
        from app.api.v1.endpoints import auth as auth_module

        async def broken_send(to_email, reset_url):
            raise OSError("SMTP down")

        monkeypatch.setattr(
            auth_module.email_service, "send_password_reset_email", broken_send
        )
        r = client.post(f"{API}/auth/forgot-password", json={"email": user_dict["email"]})
        assert r.status_code == 200  # fails safely, no stack trace leaked

    def test_reset_token_expiry_and_type_binding(self):
        token = create_password_reset_token("someone@example.com")
        payload = decode_password_reset_token(token)
        # Expires ~1 hour from now.
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        remaining = (exp - datetime.now(UTC)).total_seconds()
        assert 3500 < remaining <= 3600

        # An ACCESS token must not be usable as a RESET token.
        access = create_access_token("someone@example.com")
        assert decode_password_reset_token(access) is None


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_valid_token_resets_password(self, client, user_dict):
        token = create_password_reset_token(user_dict["email"])
        r = client.post(f"{API}/auth/reset-password", json={
            "token": token, "new_password": "FreshPassword789",
        })
        assert r.status_code == 200

        # Old password fails, new one works.
        old = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"], "password": user_dict["password"]})
        assert old.status_code == 401
        new = client.post(f"{API}/auth/login", data={
            "username": user_dict["email"], "password": "FreshPassword789"})
        assert new.status_code == 200

    def test_invalid_signature_rejected(self, client, user_dict):
        forged = jwt.encode(
            {"sub": user_dict["email"], "type": "password_reset",
             "exp": datetime.now(UTC) + timedelta(hours=1)},
            "wrong-secret", algorithm=settings.ALGORITHM,
        )
        r = client.post(f"{API}/auth/reset-password", json={
            "token": forged, "new_password": "HackedPassword1"})
        assert r.status_code == 400

    def test_expired_token_rejected(self, client, user_dict):
        expired = jwt.encode(
            {"sub": user_dict["email"], "type": "password_reset",
             "exp": datetime.now(UTC) - timedelta(minutes=1)},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM,
        )
        r = client.post(f"{API}/auth/reset-password", json={
            "token": expired, "new_password": "TooLatePass123"})
        assert r.status_code == 400

    def test_malformed_token_rejected(self, client):
        r = client.post(f"{API}/auth/reset-password", json={
            "token": "!!!not-a-jwt!!!", "new_password": "Anything1234"})
        assert r.status_code == 400

    def test_access_token_cannot_reset_password(self, client, user_dict):
        access = create_access_token(user_dict["email"])
        r = client.post(f"{API}/auth/reset-password", json={
            "token": access, "new_password": "SneakyPassword1"})
        assert r.status_code == 400

    def test_weak_new_password_rejected(self, client, user_dict):
        token = create_password_reset_token(user_dict["email"])
        r = client.post(f"{API}/auth/reset-password", json={
            "token": token, "new_password": "short"})
        assert r.status_code == 422

    def test_token_for_nonexistent_user_rejected(self, client):
        token = create_password_reset_token("gone@example.com")
        r = client.post(f"{API}/auth/reset-password", json={
            "token": token, "new_password": "Whatever1234"})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Full end-to-end authentication journey
# ---------------------------------------------------------------------------

def test_end_to_end_auth_journey(client, monkeypatch):
    from app.api.v1.endpoints import auth as auth_module

    captured = {}

    async def fake_send(to_email, reset_url):
        captured["url"] = reset_url

    monkeypatch.setattr(
        auth_module.email_service, "send_password_reset_email", fake_send
    )

    # 1. Register
    creds = {"full_name": "E2E User", "email": "e2e@example.com", "password": "FirstPass123"}
    assert client.post(f"{API}/auth/register", json=creds).status_code == 201

    # 2. Login
    login = client.post(f"{API}/auth/login", data={
        "username": creds["email"], "password": creds["password"]})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 3. Current user
    me = client.get(f"{API}/users/me", headers=headers)
    assert me.status_code == 200 and me.json()["email"] == creds["email"]

    # 4. Change password
    cp = client.post(f"{API}/users/me/change-password", headers=headers, json={
        "current_password": creds["password"], "new_password": "SecondPass456"})
    assert cp.status_code == 200

    # 5. Re-login with new password
    relogin = client.post(f"{API}/auth/login", data={
        "username": creds["email"], "password": "SecondPass456"})
    assert relogin.status_code == 200

    # 6. Logout behavior (stateless JWT): without the client token,
    #    protected calls fail again.
    anon = client.get(f"{API}/users/me")
    assert anon.status_code == 401

    # 7. Forgot password -> capture reset email
    fp = client.post(f"{API}/auth/forgot-password", json={"email": creds["email"]})
    assert fp.status_code == 200
    assert "url" in captured

    # 8. Reset through the emailed link's token
    reset_token = captured["url"].split("token=", 1)[1]
    rp = client.post(f"{API}/auth/reset-password", json={
        "token": reset_token, "new_password": "ThirdPass789"})
    assert rp.status_code == 200

    # 9. Final login with reset password; previous password dead.
    final = client.post(f"{API}/auth/login", data={
        "username": creds["email"], "password": "ThirdPass789"})
    assert final.status_code == 200
    stale = client.post(f"{API}/auth/login", data={
        "username": creds["email"], "password": "SecondPass456"})
    assert stale.status_code == 401
