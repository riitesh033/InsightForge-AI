import asyncio
import pandas as pd
import pytest

from app.core.config import settings
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.services.insights import (
    AIProviderError,
    calculate_quality_score_details,
    generate_dataset_explanation,
)
from app.services.profiling import profile_dataframe
from app.services.report import generate_analysis_report


def test_profile_computes_verified_metrics_and_iqr_bounds():
    frame = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "age": [10, 20, 20, 30, 100],
            "salary": [100, 200, 200, 400, 500],
            "department": ["A", "B", "B", "B", None],
        }
    )

    profile = profile_dataframe(frame)

    assert profile["summary"]["rows"] == 5
    assert profile["summary"]["columns"] == 4
    assert profile["summary"]["missing_cells"] == 1
    assert profile["column_info"][1]["dtype"] == "integer"
    assert profile["column_info"][2]["dtype"] == "integer"
    assert profile["column_info"][3]["dtype"] == "string"
    assert profile["missing_values"]["department"] == {
        "count": 1,
        "percent": 20.0,
    }
    assert profile["duplicates"] == {
        "count": 1,
        "percentage": 20.0,
        "has_duplicates": True,
    }
    assert profile["statistics"]["age"]["mean"] == 36
    assert profile["statistics"]["age"]["median"] == 20
    assert profile["statistics"]["age"]["q1"] == 20
    assert profile["statistics"]["age"]["q3"] == 30
    assert profile["statistics"]["department"]["top"] == "B"
    assert profile["statistics"]["department"]["freq"] == 3
    assert profile["outliers"]["age"]["count"] == 1
    assert profile["outliers"]["age"]["percentage"] == 20
    assert profile["outliers"]["age"]["lower_bound"] == 5
    assert profile["outliers"]["age"]["upper_bound"] == 45
    assert profile["correlations"]["age"]["salary"] is not None


def test_quality_score_is_weighted_deterministic_and_explains_penalties():
    profile = profile_dataframe(
        pd.DataFrame(
            {
                "age": [10, 20, 20, 30, 100],
                "salary": [100, 200, 200, 400, 500],
                "department": ["A", "B", "B", "B", None],
            }
        )
    )
    details = calculate_quality_score_details(profile)

    assert details["score"] == 89
    assert details["factors"] == {
        "missing_values_penalty": 3.0,
        "duplicate_rows_penalty": 5.0,
        "potential_outliers_penalty": 3.0,
    }
    assert calculate_quality_score_details(profile) == details


def test_profile_handles_empty_text_only_single_numeric_and_constant_columns():
    empty = profile_dataframe(pd.DataFrame(columns=["a", "b"]))
    assert empty["summary"]["rows"] == 0
    assert empty["summary"]["columns"] == 2
    assert empty["correlations"] == {}
    assert calculate_quality_score_details(empty)["score"] == 0

    text_only = profile_dataframe(pd.DataFrame({"label": ["x", "y", "x"]}))
    assert text_only["correlations"] == {}
    assert text_only["statistics"]["label"]["unique"] == 2

    one_numeric = profile_dataframe(pd.DataFrame({"value": [1, 2, 3]}))
    assert one_numeric["correlations"] == {}

    constant = profile_dataframe(pd.DataFrame({"constant": [4, 4, 4, 4]}))
    assert constant["correlations"] == {}
    assert constant["outliers"]["constant"]["count"] == 0


def test_profile_preserves_input_and_handles_missing_heavy_numeric_data():
    frame = pd.DataFrame({"amount": [None, None, 5.0, None]})
    original = frame.copy(deep=True)

    profile = profile_dataframe(frame)

    pd.testing.assert_frame_equal(frame, original)
    assert profile["missing_values"]["amount"]["count"] == 3
    assert profile["missing_values"]["amount"]["percent"] == 75.0
    assert profile["statistics"]["amount"]["count"] == 1
    assert profile["outliers"]["amount"]["count"] == 0


def _upload_csv(client, headers, monkeypatch, tmp_path, content=b"id,age,salary\n1,25,50000\n2,30,60000\n3,35,70000\n"):
    monkeypatch.setattr(settings, "DATASET_STORAGE_DIR", str(tmp_path))
    return client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={
            "file": (
                "intelligence.csv",
                content,
                "text/csv",
            )
        },
    )


def test_analysis_api_returns_profile_contract_and_owner_scoped_explanation(
    client, auth_headers, monkeypatch, tmp_path, db
):
    upload = _upload_csv(client, auth_headers, monkeypatch, tmp_path)
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["id"]

    response = client.get(
        f"/api/v1/analysis/{dataset_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    profile = response.json()["verified_analysis"]
    assert profile["dataset"]["rows"] == 3
    assert profile["dataset"]["columns"] == 3
    assert profile["dataset"]["file_type"] == "csv"
    assert profile["dataset"]["uploaded_at"]
    assert profile["column_info"][1]["dtype"] == "integer"
    assert profile["column_info"][1]["pandas_dtype"].startswith("int")
    assert profile["statistics"][0]["count"] == 3
    assert profile["statistics"][0]["median"] is not None
    assert profile["data_quality"]["score_factors"]

    generated_facts = []

    async def explanation(facts):
        generated_facts.append(facts)
        return "The dataset contains 3 rows across 3 columns, with a 100/100 quality score."

    monkeypatch.setattr(
        "app.api.v1.endpoints.analysis.generate_dataset_explanation",
        explanation,
    )
    explanation_response = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=auth_headers,
    )
    assert explanation_response.status_code == 200
    assert explanation_response.json() == {
        "available": True,
        "explanation": (
            "The dataset contains 3 rows across 3 columns, "
            "with a 100/100 quality score."
        ),
    }
    assert generated_facts[0]["dataset"]["rows"] == 3
    stored = db.query(Analysis).filter_by(dataset_id=dataset_id).one()
    assert stored.summary["ai_explanation"] == explanation_response.json()["explanation"]
    stored_dataset = db.query(Dataset).filter_by(id=dataset_id).one()
    pdf = generate_analysis_report(stored_dataset, stored)
    assert pdf.read(5) == b"%PDF-"

    def unexpected_call(_facts):
        raise AssertionError("A cached explanation should be reused.")

    monkeypatch.setattr(
        "app.api.v1.endpoints.analysis.generate_dataset_explanation",
        unexpected_call,
    )
    cached = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=auth_headers,
    )
    assert cached.status_code == 200
    assert cached.json()["available"] is True


def test_explanation_endpoint_gracefully_handles_provider_unavailability_and_ownership(
    client, auth_headers, monkeypatch, tmp_path
):
    upload = _upload_csv(client, auth_headers, monkeypatch, tmp_path)
    assert upload.status_code == 201
    dataset_id = upload.json()["id"]

    async def unavailable(_facts):
        return None

    monkeypatch.setattr(
        "app.api.v1.endpoints.analysis.generate_dataset_explanation",
        unavailable,
    )
    response = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert "deterministic dataset analysis is still available" in response.json()["explanation"]

    second_user = {
        "full_name": "Other Intelligence User",
        "email": "other-intelligence@example.com",
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
    denied = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=other_headers,
    )
    assert denied.status_code == 404


def test_analysis_recommendations_reflect_actual_missing_duplicates_and_outliers(
    client, auth_headers, monkeypatch, tmp_path
):
    content = (
        b"salary,age,city\n"
        b"10,1,A\n"
        b"10,1,A\n"
        b"20,2,\n"
        b"30,3,C\n"
        b"1000,4,D\n"
    )
    upload = _upload_csv(
        client,
        auth_headers,
        monkeypatch,
        tmp_path,
        content=content,
    )
    assert upload.status_code == 201, upload.text

    response = client.get(
        f"/api/v1/analysis/{upload.json()['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    findings = response.json()["insights"]["insights"]
    findings_by_title = {item["title"]: item for item in findings}

    missing = findings_by_title["Missing values detected in city"]
    assert "1 missing value" in missing["finding"]
    assert "city" in missing["recommended_action"]

    duplicates = findings_by_title["Duplicate records detected"]
    assert "1 duplicate record" in duplicates["finding"]
    assert "20.00%" in [item["value"] for item in duplicates["evidence"]]

    outlier = findings_by_title["Potential outliers detected in salary"]
    assert "1 potential outlier" in outlier["finding"]
    assert "not automatically an error" in outlier["interpretation"]


def test_ai_explanation_uses_provider_fallback_and_rejects_unsupported_numbers(
    monkeypatch,
):
    facts = {
        "dataset": {"rows": 10, "columns": 2},
        "data_quality": {"quality_score": 82},
    }

    async def supported(_prompt):
        return "The dataset has 10 rows and quality score 82."

    monkeypatch.setattr("app.services.insights.generate_ai_response", supported)
    assert asyncio.run(generate_dataset_explanation(facts)) == (
        "The dataset has 10 rows and quality score 82."
    )

    async def unsupported(_prompt):
        return "The dataset has 99 rows and quality score 82."

    monkeypatch.setattr("app.services.insights.generate_ai_response", unsupported)
    assert asyncio.run(generate_dataset_explanation(facts)) is None

    async def provider_unavailable(_prompt):
        raise AIProviderError("unavailable")

    monkeypatch.setattr(
        "app.services.insights.generate_ai_response",
        provider_unavailable,
    )
    assert asyncio.run(generate_dataset_explanation(facts)) is None
