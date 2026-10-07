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


def test_admin_system_health_reports_live_storage_and_db_status(
    client, auth_headers, user_dict, db
):
    from app.models.dataset import Dataset
    from app.models.user import User

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()

    db.add(
        Dataset(
            owner_id=user.id,
            filename="stored.csv",
            original_filename="stored.csv",
            file_type="csv",
            file_size=2048,
            file_path="stored.csv",
            rows=10,
            columns=2,
        )
    )
    db.commit()

    response = client.get(
        f"{API}/admin/system-health",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["backend_status"] == "Operational"
    assert body["database_status"] == "Healthy"
    # Storage usage is derived from stored dataset records, so it must
    # reflect cloud-backed datasets and not only local staging files.
    assert body["storage_usage_mb"] == round(2048 / (1024 * 1024), 2)


def test_admin_dataset_purge_removes_analysis_and_chat_rows(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    from app.models.analysis import Analysis
    from app.models.chat_session import ChatSession
    from app.models.dataset import Dataset
    from app.models.user import User
    from app.services.dataset_storage import resolve_dataset_path
    from app.core.config import settings

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()

    monkeypatch.setattr(settings, "DATASET_STORAGE_DIR", str(tmp_path))
    upload = client.post(
        f"{API}/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "normal.csv",
                b"id,age\n1,25\n2,30\n",
                "application/octet-stream",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["id"]
    stored_path = resolve_dataset_path(upload.json()["file_path"])
    assert stored_path.is_file()

    chat = client.post(
        f"{API}/chat/{dataset_id}",
        headers=auth_headers,
        json={"message": "How many rows are in this dataset?"},
    )
    assert chat.status_code == 200, chat.text

    purged = client.delete(
        f"{API}/admin/datasets/{dataset_id}",
        headers=auth_headers,
    )
    assert purged.status_code == 200, purged.text

    assert db.query(Dataset).filter(Dataset.id == dataset_id).count() == 0
    assert db.query(Analysis).filter(Analysis.dataset_id == dataset_id).count() == 0
    assert (
        db.query(ChatSession)
        .filter(ChatSession.dataset_id == dataset_id)
        .count()
        == 0
    )
    # The stored file must be removed, not just the database row.
    assert not stored_path.exists()

