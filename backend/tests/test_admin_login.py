from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User

API = "/api/v1"
ADMIN_LOGIN = f"{API}/auth/admin/login"


def test_admin_login_returns_standard_token_without_credentials(
    client, user_dict, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()

    response = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": user_dict["password"],
        },
    )

    assert response.status_code == 200, response.text
    assert set(response.json()) == {"access_token", "token_type"}
    assert response.json()["token_type"] == "bearer"
    assert user_dict["password"] not in response.text
    assert "hashed_password" not in response.text
    assert user.hashed_password not in response.text
    assert (
        client.get(
            f"{API}/admin/dashboard",
            headers={"Authorization": f"Bearer {response.json()['access_token']}"},
        ).status_code
        == 200
    )


def test_admin_login_rejects_wrong_password_unknown_and_normal_user(
    client, user_dict, db
):
    normal_login = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": user_dict["password"],
        },
    )
    wrong_password = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": "WrongPassword123!",
        },
    )
    unknown_user = client.post(
        ADMIN_LOGIN,
        json={
            "email": "missing-user@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert normal_login.status_code == wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert normal_login.json()["detail"] == wrong_password.json()["detail"]
    assert unknown_user.json()["detail"] == wrong_password.json()["detail"]

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()
    wrong_admin_password = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": "WrongPassword123!",
        },
    )
    assert wrong_admin_password.status_code == 401


def test_inactive_admin_cannot_login(client, user_dict, db):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    user.is_active = False
    db.commit()

    response = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": user_dict["password"],
        },
    )

    assert response.status_code == 401


def test_expired_malformed_and_missing_tokens_cannot_access_admin(
    client, user_dict
):
    expired_token = jwt.encode(
        {
            "sub": user_dict["email"],
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert client.get(f"{API}/admin/dashboard").status_code == 401
    assert client.get(
        f"{API}/admin/dashboard",
        headers={"Authorization": "Bearer malformed-token"},
    ).status_code == 401
    assert client.get(
        f"{API}/admin/dashboard",
        headers={"Authorization": f"Bearer {expired_token}"},
    ).status_code == 401


def test_forged_admin_jwt_claim_does_not_grant_admin_access(
    client, user_dict
):
    forged_claim_token = jwt.encode(
        {
            "sub": user_dict["email"],
            "is_superuser": True,
            "role": "admin",
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        f"{API}/admin/dashboard",
        headers={"Authorization": f"Bearer {forged_claim_token}"},
    )

    assert response.status_code == 403


def test_cli_interactively_changes_existing_admin_password(
    client, db, user_dict, monkeypatch, capsys
):
    from app.scripts import create_admin

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    original_hash = user.hashed_password
    monkeypatch.setattr(create_admin, "SessionLocal", lambda: _session_context(db))
    monkeypatch.setattr("builtins.input", lambda _prompt: user_dict["email"])
    passwords = iter(["NewStrongPassword123!", "NewStrongPassword123!"])
    monkeypatch.setattr(
        create_admin.getpass,
        "getpass",
        lambda _prompt: next(passwords),
    )
    monkeypatch.setattr("sys.argv", ["create_admin"])

    assert create_admin.main() == 0
    db.refresh(user)
    output = capsys.readouterr()
    assert "now configured as an administrator" in output.out
    assert "NewStrongPassword123!" not in output.out
    assert user.is_superuser is True
    assert user.hashed_password != original_hash
    assert verify_password("NewStrongPassword123!", user.hashed_password)
    assert not verify_password(user_dict["password"], user.hashed_password)
    old_password_response = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": user_dict["password"],
        },
    )
    new_password_response = client.post(
        ADMIN_LOGIN,
        json={
            "email": user_dict["email"],
            "password": "NewStrongPassword123!",
        },
    )
    assert old_password_response.status_code == 401
    assert new_password_response.status_code == 200


def test_cli_rejects_weak_password_without_promoting_user(
    db, user_dict, monkeypatch, capsys
):
    from app.scripts import create_admin

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    original_hash = user.hashed_password
    monkeypatch.setattr(create_admin, "SessionLocal", lambda: _session_context(db))
    monkeypatch.setattr("builtins.input", lambda _prompt: user_dict["email"])
    passwords = iter(["short", "short"])
    monkeypatch.setattr(
        create_admin.getpass,
        "getpass",
        lambda _prompt: next(passwords),
    )
    monkeypatch.setattr("sys.argv", ["create_admin"])

    assert create_admin.main() == 2
    db.refresh(user)
    output = capsys.readouterr()
    assert "at least 12 characters" in output.err
    assert "short" not in output.out
    assert user.is_superuser is False
    assert user.hashed_password == original_hash


def test_cli_refuses_missing_users_without_password_prompt(
    db, monkeypatch, capsys
):
    from app.scripts import create_admin

    monkeypatch.setattr(create_admin, "SessionLocal", lambda: _session_context(db))
    monkeypatch.setattr("builtins.input", lambda _prompt: "not-found@example.com")
    monkeypatch.setattr(
        create_admin.getpass,
        "getpass",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("must not prompt")),
    )
    monkeypatch.setattr("sys.argv", ["create_admin"])

    assert create_admin.main() == 1
    assert "through the normal application" in capsys.readouterr().err
    assert db.query(User).count() == 0


def test_cli_check_reports_status_without_asking_for_password(
    db, user_dict, monkeypatch, capsys
):
    from app.scripts import create_admin

    monkeypatch.setattr(create_admin, "SessionLocal", lambda: _session_context(db))
    monkeypatch.setattr("builtins.input", lambda _prompt: user_dict["email"])
    monkeypatch.setattr(
        create_admin.getpass,
        "getpass",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("must not prompt")),
    )
    monkeypatch.setattr("sys.argv", ["create_admin", "--check"])

    assert create_admin.main() == 0
    assert "not enabled" in capsys.readouterr().out


def _session_context(db):
    from contextlib import nullcontext

    return nullcontext(db)
