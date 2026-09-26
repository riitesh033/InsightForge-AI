import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints import health as health_endpoint
from app.main import app


def test_root_and_health_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/api/v1/health").json()["status"] == "healthy"


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
