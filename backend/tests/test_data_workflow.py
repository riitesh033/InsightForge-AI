import asyncio
from pathlib import Path

import pandas as pd
import pytest

from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.subscription import PlanType, Subscription, SubscriptionStatus
from app.models.user import User
from app.services import ai_provider, dataset as dataset_service
from app.services.dataset_storage import (
    dataset_storage_root,
    resolve_dataset_path,
)


def grant_pro_plan(db, user_dict):
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
        )
    )
    db.commit()


def upload_file(client, headers, monkeypatch, tmp_path, filename, content):
    monkeypatch.setattr(dataset_service, "UPLOAD_DIR", tmp_path)
    return client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": (filename, content, "application/octet-stream")},
    )


@pytest.mark.parametrize(
    ("filename", "expected_rows", "expected_columns"),
    [
        ("normal.csv", 3, 3),
        ("missing.csv", 3, 2),
        ("duplicates.csv", 3, 2),
        ("outliers.csv", 6, 1),
        ("categorical.csv", 4, 1),
        ("mixed.csv", 3, 2),
        ("empty.csv", 0, 2),
        ("one-row.csv", 1, 2),
        ("wide.csv", 2, 120),
        ("workbook.xlsx", 3, 2),
    ],
)
def test_upload_profiles_and_persists_supported_fixtures(
    client, auth_headers, db, monkeypatch, tmp_path, workflow_files,
    filename, expected_rows, expected_columns,
):
    response = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        filename,
        workflow_files[filename],
    )

    assert response.status_code == 201, response.text
    uploaded = response.json()
    stored_dataset = db.query(Dataset).filter_by(id=uploaded["id"]).one()
    assert uploaded["rows"] == expected_rows
    assert uploaded["columns"] == expected_columns
    assert Path(uploaded["file_path"]).parent == tmp_path
    assert Path(uploaded["file_path"]).is_file()
    assert stored_dataset.file_path == uploaded["file_path"]
    assert resolve_dataset_path(stored_dataset.file_path).is_file()

    analysis = db.query(Analysis).filter(
        Analysis.dataset_id == uploaded["id"]
    ).one()
    assert 0 <= analysis.quality_score <= 100
    assert isinstance(analysis.summary, dict)
    assert isinstance(analysis.statistics, dict)
    assert isinstance(analysis.correlations, dict)
    assert isinstance(analysis.outliers, dict)
    assert analysis.summary["rows"] == expected_rows
    assert analysis.summary["columns"] == expected_columns
    assert analysis.summary["memory_usage"] >= 0
    if filename == "missing.csv":
        assert analysis.missing_values["age"]["count"] == 1
        assert analysis.missing_values["city"]["count"] == 1
    elif filename == "duplicates.csv":
        assert analysis.duplicates["count"] == 1
    elif filename == "outliers.csv":
        assert analysis.outliers["value"] == 1
    elif filename == "categorical.csv":
        assert analysis.statistics["color"]["freq"] == 2
    elif filename == "normal.csv":
        assert analysis.statistics["age"]["mean"] == 30
        assert analysis.correlations["age"]["salary"] == 1.0


def test_upload_rejects_unreadable_empty_file_without_persisting(
    client, auth_headers, db, monkeypatch, tmp_path, workflow_files
):
    response = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "invalid-empty.csv",
        workflow_files["invalid-empty.csv"],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to read dataset."
    assert db.query(Dataset).count() == 0
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_unsupported_extension(
    client, auth_headers, db, monkeypatch, tmp_path
):
    response = upload_file(
        client, auth_headers, monkeypatch, tmp_path, "dataset.json", b"{}"
    )

    assert response.status_code == 400
    assert db.query(Dataset).count() == 0


def test_upload_enforces_file_size(
    client, auth_headers, db, monkeypatch, tmp_path, workflow_files
):
    from app.services.payment import payment_service

    monkeypatch.setitem(
        payment_service.plans["free"]["limits"],
        "max_file_size_mb",
        0,
    )
    response = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLAN_LIMIT_REACHED"
    assert db.query(Dataset).count() == 0


def test_upload_sanitizes_client_filename_and_uses_generated_storage_name(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    response = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        r"..\private\dataset.csv",
        workflow_files["normal.csv"],
    )

    assert response.status_code == 201, response.text
    uploaded = response.json()
    assert uploaded["original_filename"] == "dataset.csv"
    assert Path(uploaded["filename"]).name == uploaded["filename"]
    assert uploaded["filename"] != uploaded["original_filename"]


def test_analysis_endpoint_returns_verified_profile(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    dataset_id = upload.json()["id"]

    response = client.get(
        f"/api/v1/analysis/{dataset_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    verified = body["verified_analysis"]
    assert verified["dataset"]["rows"] == 3
    assert verified["dataset"]["columns"] == 3
    assert verified["statistics"]
    assert verified["correlations"]
    assert 0 <= verified["data_quality"]["quality_score"] <= 100


def test_dataset_analysis_and_cleaning_are_owner_scoped(
    client, auth_headers, db, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    dataset_id = upload.json()["id"]
    second_user = {
        "full_name": "Other Tester",
        "email": "other@example.com",
        "password": "OtherSecret123",
    }
    assert client.post("/api/v1/auth/register", json=second_user).status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )
    other_headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    assert client.get(
        f"/api/v1/analysis/{dataset_id}", headers=other_headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/cleaning/{dataset_id}/preview", headers=other_headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/datasets/{dataset_id}/download", headers=other_headers
    ).status_code == 404
    assert db.query(Dataset).filter(Dataset.id == dataset_id).count() == 1


def test_cleaning_preview_apply_and_download_preserve_original(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "missing.csv",
        workflow_files["missing.csv"],
    )
    dataset = upload.json()
    original_path = Path(dataset["file_path"])
    original_bytes = original_path.read_bytes()

    preview = client.post(
        f"/api/v1/cleaning/{dataset['id']}/preview",
        headers=auth_headers,
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["preview"]["missing_values_filled"] == 2

    applied = client.post(
        f"/api/v1/cleaning/{dataset['id']}/apply",
        headers=auth_headers,
    )
    assert applied.status_code == 200, applied.text
    summary = applied.json()["preview"]
    assert summary["missing_values_after"] == 0
    assert original_path.read_bytes() == original_bytes

    cleaned = pd.read_csv(applied.json()["preview"]["cleaned_file_path"])
    assert cleaned["age"].isna().sum() == 0
    assert cleaned["city"].isna().sum() == 0

    download = client.get(
        f"/api/v1/cleaning/{dataset['id']}/download",
        headers=auth_headers,
    )
    assert download.status_code == 200
    assert download.content.startswith(b"age,city")


def test_xlsx_cleaning_preview_reads_uploaded_file(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "workbook.xlsx",
        workflow_files["workbook.xlsx"],
    )

    response = client.post(
        f"/api/v1/cleaning/{upload.json()['id']}/preview",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["preview"]["rows_before"] == 3
    assert response.json()["preview"]["columns"] == 2


def test_configured_storage_root_upload_and_legacy_resolution(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    from app.core.config import settings

    grant_pro_plan(db, user_dict)
    mounted_directory = tmp_path / "mounted-datasets"
    monkeypatch.setattr(settings, "DATASET_STORAGE_DIR", str(mounted_directory))
    root = dataset_storage_root()
    root.mkdir(parents=True)
    monkeypatch.setattr(dataset_service, "UPLOAD_DIR", root)

    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "linux-storage.csv",
                workflow_files["normal.csv"],
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text
    dataset_id = response.json()["id"]
    stored_dataset = db.query(Dataset).filter_by(id=dataset_id).one()
    uploaded_file = root / stored_dataset.filename
    assert Path(stored_dataset.file_path) == uploaded_file
    assert uploaded_file.is_file()

    preview = client.post(
        f"/api/v1/cleaning/{dataset_id}/preview",
        headers=auth_headers,
    )
    assert preview.status_code == 200, preview.text

    assert resolve_dataset_path(
        f"app/uploads/datasets/{stored_dataset.filename}"
    ) == uploaded_file.resolve()


def test_cleaning_preview_rejects_unauthorized_invalid_token_and_missing_dataset(
    client, auth_headers
):
    preview_url = "/api/v1/cleaning/9/preview"

    unauthorized = client.post(preview_url)
    assert unauthorized.status_code == 401

    malformed_token = client.post(
        preview_url,
        headers={"Authorization": "Bearer malformed-token"},
    )
    assert malformed_token.status_code == 401

    missing_dataset = client.post(
        "/api/v1/cleaning/2147483647/preview",
        headers=auth_headers,
    )
    assert missing_dataset.status_code == 404
    assert missing_dataset.json() == {"detail": "Dataset not found."}

    for response in (unauthorized, malformed_token, missing_dataset):
        assert "Traceback" not in response.text


def test_cleaning_removes_duplicates_and_normalizes_categories(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    payload = b"category,value\n red ,1\nred,1\n blue ,2\n"
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "categories.csv",
        payload,
    )
    applied = client.post(
        f"/api/v1/cleaning/{upload.json()['id']}/apply",
        headers=auth_headers,
    )

    assert applied.status_code == 200, applied.text
    assert applied.json()["preview"]["duplicates_removed"] == 1
    cleaned = pd.read_csv(applied.json()["preview"]["cleaned_file_path"])
    assert cleaned["category"].tolist() == ["red", "blue"]


def test_cleaning_download_before_apply_returns_not_found(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    response = client.get(
        f"/api/v1/cleaning/{upload.json()['id']}/download",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cleaned dataset has not been generated yet."


def test_chat_persists_session_and_messages(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    response = client.post(
        f"/api/v1/chat/{upload.json()['id']}",
        headers=auth_headers,
        json={"message": "How many rows are in this dataset?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dataset_id"] == upload.json()["id"]
    assert body["session_id"]
    assert "3 rows" in body["answer"]
    assert [message["role"] for message in body["messages"]] == [
        "user",
        "assistant",
    ]


def test_new_chat_title_uses_first_saved_user_message(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    dataset_id = upload.json()["id"]
    created = client.post(
        f"/api/v1/chat/{dataset_id}/sessions",
        headers=auth_headers,
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]
    assert created.json()["title"] == "New Chat"

    response = client.post(
        f"/api/v1/chat/{dataset_id}",
        headers=auth_headers,
        json={
            "message": "How many rows are in this dataset?",
            "session_id": session_id,
        },
    )
    assert response.status_code == 200, response.text
    second_created = client.post(
        f"/api/v1/chat/{dataset_id}/sessions",
        headers=auth_headers,
    )
    assert second_created.status_code == 200, second_created.text
    second_id = second_created.json()["id"]
    second_response = client.post(
        f"/api/v1/chat/{dataset_id}",
        headers=auth_headers,
        json={
            "message": "How many rows are in this dataset?",
            "session_id": second_id,
        },
    )
    assert second_response.status_code == 200, second_response.text

    sessions = client.get(
        f"/api/v1/chat/{dataset_id}/sessions",
        headers=auth_headers,
    )

    assert sessions.status_code == 200
    assert [item["id"] for item in sessions.json()] == [second_id, session_id]
    assert sessions.json()[1]["title"] == "How many rows are in this dataset?"
    assert sessions.json()[1]["last_message"] == response.json()["answer"]

    refreshed_first = client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=auth_headers,
    )
    refreshed_second = client.get(
        f"/api/v1/chat/sessions/{second_id}",
        headers=auth_headers,
    )
    assert refreshed_first.status_code == refreshed_second.status_code == 200
    assert [item["content"] for item in refreshed_first.json()["messages"]] == [
        "How many rows are in this dataset?",
        response.json()["answer"],
    ]
    assert [item["content"] for item in refreshed_second.json()["messages"]] == [
        "How many rows are in this dataset?",
        second_response.json()["answer"],
    ]


def test_chat_provider_failure_returns_safe_answer_and_persists_messages(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )

    async def fail_provider(_prompt):
        raise ai_provider.AIProviderError("provider detail must not escape")

    monkeypatch.setattr("app.services.chat.generate_ai_response", fail_provider)
    response = client.post(
        f"/api/v1/chat/{upload.json()['id']}",
        headers=auth_headers,
        json={"message": "Explain the relationship between the data fields."},
    )

    assert response.status_code == 200, response.text
    assert "temporarily unavailable" in response.json()["answer"]
    assert "provider detail" not in response.text
    assert len(response.json()["messages"]) == 2


def test_chat_empty_provider_answer_returns_safe_fallback(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )

    async def empty_provider(_prompt):
        return "  "

    monkeypatch.setattr("app.services.chat.generate_ai_response", empty_provider)
    response = client.post(
        f"/api/v1/chat/{upload.json()['id']}",
        headers=auth_headers,
        json={"message": "Explain the relationship between the data fields."},
    )

    assert response.status_code == 200
    assert "temporarily unavailable" in response.json()["answer"]
    assert response.json()["messages"][-1]["content"] == response.json()["answer"]


def test_chat_rejects_unauthenticated_and_unowned_requests(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    url = f"/api/v1/chat/{upload.json()['id']}"

    assert client.post(url, json={"message": "How many rows?"}).status_code == 401
    second_user = {
        "full_name": "Chat Viewer",
        "email": "chat-viewer@example.com",
        "password": "OtherSecret123",
    }
    assert client.post(
        "/api/v1/auth/register", json=second_user
    ).status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )
    other_headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }
    assert client.post(
        url,
        headers=other_headers,
        json={"message": "How many rows?"},
    ).status_code == 404

    created_session = client.post(
        f"{url}/sessions",
        headers=auth_headers,
    )
    assert created_session.status_code == 200
    session_id = created_session.json()["id"]
    session_url = f"/api/v1/chat/sessions/{session_id}"

    assert client.get(session_url).status_code == 401
    assert client.get(session_url, headers=other_headers).status_code == 404
    assert client.delete(session_url, headers=other_headers).status_code == 404
    assert client.get(
        f"{url}/sessions",
        headers=other_headers,
    ).status_code == 404
    assert client.delete(session_url, headers=auth_headers).status_code == 204
    assert client.get(session_url, headers=auth_headers).status_code == 404


def test_report_download_generates_pdf(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    response = client.get(
        f"/api/v1/reports/{upload.json()['id']}/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_report_handles_missing_source_file_without_exception_details(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    Path(upload.json()["file_path"]).unlink()

    response = client.get(
        f"/api/v1/reports/{upload.json()['id']}/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "file_path" not in response.text
    assert "Traceback" not in response.text


def test_analysis_report_handles_missing_source_file_safely(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    Path(upload.json()["file_path"]).unlink()

    response = client.get(
        f"/api/v1/analysis/{upload.json()['id']}/report",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "file_path" not in response.text
    assert "Traceback" not in response.text


def test_ai_router_falls_back_after_provider_failure(monkeypatch):
    calls = []

    async def fail_gemini(_prompt):
        calls.append("gemini")
        raise ai_provider.AIProviderError("unavailable")

    async def successful_openrouter(_prompt):
        calls.append("openrouter")
        return "A deterministic mocked answer."

    async def unused_ollama(_prompt):
        calls.append("ollama")
        raise AssertionError("Ollama should not be needed")

    monkeypatch.setattr(ai_provider.settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(ai_provider, "generate_with_gemini", fail_gemini)
    monkeypatch.setattr(
        ai_provider, "generate_with_openrouter", successful_openrouter
    )
    monkeypatch.setattr(ai_provider, "generate_with_ollama", unused_ollama)

    answer = asyncio.run(ai_provider.generate_ai_response("test prompt"))

    assert answer == "A deterministic mocked answer."
    assert calls == ["gemini", "openrouter"]


@pytest.mark.parametrize("failure", ["malformed", "timeout", "empty"])
def test_ai_router_reports_failure_when_all_mocked_providers_fail(
    monkeypatch, failure
):
    async def fail(_prompt):
        if failure == "empty":
            return "  "
        if failure == "timeout":
            raise TimeoutError("simulated provider timeout")
        raise ValueError("simulated malformed provider response")

    monkeypatch.setattr(ai_provider.settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(ai_provider, "generate_with_gemini", fail)
    monkeypatch.setattr(ai_provider, "generate_with_openrouter", fail)
    monkeypatch.setattr(ai_provider, "generate_with_ollama", fail)

    with pytest.raises(ai_provider.AIProviderError):
        asyncio.run(ai_provider.generate_ai_response("test prompt"))


def test_cleaning_missing_source_returns_safe_not_found(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path, workflow_files
):
    grant_pro_plan(db, user_dict)
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    Path(upload.json()["file_path"]).unlink()

    response = client.post(
        f"/api/v1/cleaning/{upload.json()['id']}/preview",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset file not found on server."
    assert "Traceback" not in response.text


def test_report_rejects_unauthorized_dataset(
    client, auth_headers, monkeypatch, tmp_path, workflow_files
):
    upload = upload_file(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        "normal.csv",
        workflow_files["normal.csv"],
    )
    second_user = {
        "full_name": "Report Viewer",
        "email": "report-viewer@example.com",
        "password": "OtherSecret123",
    }
    client.post("/api/v1/auth/register", json=second_user)
    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )

    response = client.get(
        f"/api/v1/reports/{upload.json()['id']}/pdf",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset not found."
