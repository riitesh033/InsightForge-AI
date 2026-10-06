import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints import health as health_endpoint
from app.core.config import settings
from app.main import app


def test_root_and_health_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/api/v1/health").json()["status"] == "healthy"


def test_cleaning_preview_route_is_registered_in_application_openapi():
    route = app.openapi()["paths"]["/api/v1/cleaning/{dataset_id}/preview"]

    assert "post" in route


def test_cleaning_preview_cors_preflight(client):
    response = client.options(
        "/api/v1/cleaning/9/preview",
        headers={
            "Origin": settings.FRONTEND_URL,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,accept",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == settings.FRONTEND_URL
    assert response.headers["access-control-allow-credentials"] == "true"
    allowed_methods = {
        method.strip()
        for method in response.headers["access-control-allow-methods"].split(",")
    }
    assert {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"} <= allowed_methods
    allowed_headers = {
        header.strip().lower()
        for header in response.headers["access-control-allow-headers"].split(",")
    }
    assert {"authorization", "content-type", "accept"} <= allowed_headers

    rejected_origin = client.options(
        "/api/v1/cleaning/9/preview",
        headers={
            "Origin": "https://untrusted.invalid",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,accept",
        },
    )
    assert rejected_origin.status_code == 400
    assert "access-control-allow-origin" not in rejected_origin.headers


def test_database_health_route_reports_success(monkeypatch, client):
    class HealthySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement):
            return None

    monkeypatch.setattr(
        health_endpoint,
        "SessionLocal",
        lambda: HealthySession(),
    )

    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_database_health_route_hides_database_errors(monkeypatch, client):
    class UnhealthySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement):
            raise SQLAlchemyError("private database connection details")

    monkeypatch.setattr(
        health_endpoint,
        "SessionLocal",
        lambda: UnhealthySession(),
    )

    response = client.get("/api/v1/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_application_startup_fails_when_migrations_fail(monkeypatch):
    def fail_migrations():
        raise RuntimeError("migration failure")

    monkeypatch.setattr("app.main.ensure_migrations", fail_migrations)

    with pytest.raises(RuntimeError, match="migration failure"):
        with TestClient(app):
            pass
