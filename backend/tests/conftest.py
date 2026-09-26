"""Shared pytest fixtures for the InsightForge backend test-suite.

IMPORTANT: environment variables are set BEFORE any ``app.*`` import so that
Pydantic Settings (which is cached at module level) picks up the isolated
test configuration instead of the developer's local .env file.
"""

import os
from io import BytesIO

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/insightforge_test",
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "unit-test-secret-key-not-a-real-secret"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "false"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
# Ensure SMTP is treated as unconfigured unless a test overrides it.
for var in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
    os.environ.pop(var, None)

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.user import User

# ---------------------------------------------------------------------------
# In-memory SQLite database for isolation (never touches production data).
# JSON columns are compiled as TEXT on SQLite.
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import JSON


@compiles(JSON, "sqlite")
def _compile_json_sqlite(type_, compiler, **kw):  # pragma: no cover
    return "TEXT"


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    from app.db.base import Base  # noqa: F401 (ensures all models are imported)

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


from app.db.base import Base  # noqa: E402  (ensures ALL models are imported)


@pytest.fixture(autouse=True)
def _fresh_db():
    """Delete all rows before every test for full isolation."""
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.exec_driver_sql(f"DELETE FROM {table.name}")
    yield


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db, monkeypatch):
    monkeypatch.setattr("app.main.ensure_migrations", lambda: None)

    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def user_dict(client):
    """A registered, ordinary user."""
    payload = {
        "full_name": "Alice Tester",
        "email": "alice@example.com",
        "password": "SuperSecret123",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return payload


@pytest.fixture()
def auth_headers(client, user_dict):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": user_dict["email"], "password": user_dict["password"]},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def workflow_files():
    """Small deterministic file payloads for data-workflow tests."""
    csv_files = {
        "normal.csv": b"id,age,salary\n1,25,50000\n2,30,60000\n3,35,70000\n",
        "missing.csv": b"age,city\n20,North\n,South\n40,\n",
        "duplicates.csv": b"name,value\nA,1\nB,2\nA,1\n",
        "outliers.csv": b"value\n1\n2\n2\n3\n4\n100\n",
        "categorical.csv": b"color\nred\nblue\nred\ngreen\n",
        "mixed.csv": b"value,label\n1,valid\ntwo,other\n3,valid\n",
        "empty.csv": b"column_a,column_b\n",
        "invalid-empty.csv": b"",
        "one-row.csv": b"amount,category\n42,only\n",
    }
    wide_frame = pd.DataFrame(
        {f"column_{index}": [index, index + 1] for index in range(120)}
    )
    csv_files["wide.csv"] = wide_frame.to_csv(index=False).encode("utf-8")

    excel_buffer = BytesIO()
    pd.DataFrame(
        {"amount": [10, 20, 30], "category": ["a", "b", "a"]}
    ).to_excel(excel_buffer, index=False, engine="openpyxl")

    return {
        **csv_files,
        "workbook.xlsx": excel_buffer.getvalue(),
    }
