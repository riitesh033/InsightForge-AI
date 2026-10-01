from app.models.user import User

API = "/api/v1"


def test_normal_user_is_denied_admin_dashboard_and_review_api(
    client, auth_headers
):
    dashboard = client.get(
        f"{API}/admin/dashboard",
        headers=auth_headers,
    )
    review_queue = client.get(
        f"{API}/admin/student-verifications",
        headers=auth_headers,
    )

    assert dashboard.status_code == 403
    assert review_queue.status_code == 403


def test_admin_user_can_access_dashboard_review_queue_and_user_profile(
    client, auth_headers, user_dict, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()

    profile = client.get(f"{API}/users/me", headers=auth_headers)
    dashboard = client.get(
        f"{API}/admin/dashboard",
        headers=auth_headers,
    )
    review_queue = client.get(
        f"{API}/admin/student-verifications",
        headers=auth_headers,
    )

    assert profile.status_code == 200
    assert profile.json()["is_superuser"] is True
    assert "hashed_password" not in profile.json()
    assert dashboard.status_code == 200
    assert review_queue.status_code == 200
    assert review_queue.json()["applications"] == []


def test_admin_routes_remain_protected_from_unauthenticated_users(client):
    assert client.get(f"{API}/admin/dashboard").status_code == 401
    assert client.get(f"{API}/admin/student-verifications").status_code == 401
    assert client.get(f"{API}/users/me").status_code == 401


def test_normal_user_cannot_promote_themselves_through_profile_api(
    client, auth_headers, user_dict, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    assert user.is_superuser is False

    response = client.patch(
        f"{API}/users/me",
        headers=auth_headers,
        json={
            "full_name": "Alice Tester",
            "email": user.email,
            "is_superuser": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_superuser"] is False
    db.refresh(user)
    assert user.is_superuser is False


def test_login_token_does_not_override_database_admin_status(
    client, auth_headers, user_dict, db
):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    assert user.is_superuser is False
    assert client.get(
        f"{API}/admin/dashboard",
        headers=auth_headers,
    ).status_code == 403

    user.is_superuser = True
    db.commit()
    assert client.get(
        f"{API}/admin/dashboard",
        headers=auth_headers,
    ).status_code == 200
