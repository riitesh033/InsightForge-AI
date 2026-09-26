from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.models.dataset import Dataset
from app.models.user import User

API = "/api/v1"
GENERIC_RESET_MESSAGE = (
    "If the account exists, a password reset email has been sent."
)


def test_inactive_user_cannot_login(client, user_dict, db):
    user = db.query(User).filter(User.email == user_dict["email"]).one()
    user.is_active = False
    db.commit()

    response = client.post(f"{API}/auth/login", data={
        "username": user_dict["email"],
        "password": user_dict["password"],
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_current_user_rejects_non_string_jwt_subject(client):
    token = jwt.encode(
        {
            "sub": {"email": "alice@example.com"},
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{API}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_user_cannot_access_another_users_dataset(
    client, auth_headers, db
):
    other_user_response = client.post(f"{API}/auth/register", json={
        "full_name": "Other User",
        "email": "other@example.com",
        "password": "OtherPassword123",
    })
    assert other_user_response.status_code == 201
    other_user_id = other_user_response.json()["id"]

    dataset = Dataset(
        filename="private.csv",
        original_filename="private.csv",
        file_type="csv",
        file_size=10,
        file_path="private.csv",
        rows=1,
        columns=1,
        owner_id=other_user_id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    response = client.get(
        f"{API}/datasets/{dataset.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_non_admin_cannot_access_admin_api(client, auth_headers):
    response = client.get(
        f"{API}/admin/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_forgot_password_does_not_enumerate_accounts(
    client, user_dict, monkeypatch
):
    from app.api.v1.endpoints import auth as auth_module

    async def capture_email(to_email: str, reset_url: str) -> None:
        return None

    monkeypatch.setattr(
        auth_module.email_service,
        "send_password_reset_email",
        capture_email,
    )

    known = client.post(
        f"{API}/auth/forgot-password",
        json={"email": user_dict["email"]},
    )
    unknown = client.post(
        f"{API}/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json() == {
        "message": GENERIC_RESET_MESSAGE,
    }
    assert "reset_token" not in known.json()


def test_reset_delivery_failure_does_not_log_token_or_error_text(
    client, user_dict, monkeypatch, caplog
):
    from app.api.v1.endpoints import auth as auth_module

    token_sentinel = "sensitive-reset-token-value"

    async def failed_delivery(to_email: str, reset_url: str) -> None:
        raise OSError(token_sentinel)

    monkeypatch.setattr(
        auth_module.email_service,
        "send_password_reset_email",
        failed_delivery,
    )

    response = client.post(
        f"{API}/auth/forgot-password",
        json={"email": user_dict["email"]},
    )

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_RESET_MESSAGE}
    assert token_sentinel not in caplog.text
