import pytest
from alembic.config import Config

from app.db.database import normalize_database_url


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgresql://user:encoded%40pass@db.example/app?sslmode=require",
            "postgresql+psycopg2://user:encoded%40pass@db.example/app?sslmode=require",
        ),
        (
            "postgres://user:encoded%40pass@db.example/app?sslmode=require",
            "postgresql+psycopg2://user:encoded%40pass@db.example/app?sslmode=require",
        ),
        (
            "postgresql+psycopg2://user:encoded%40pass@db.example/app",
            "postgresql+psycopg2://user:encoded%40pass@db.example/app",
        ),
        (
            "postgresql+psycopg://user:encoded%40pass@db.example/app",
            "postgresql+psycopg://user:encoded%40pass@db.example/app",
        ),
    ],
)
def test_normalize_database_url(database_url: str, expected: str) -> None:
    assert normalize_database_url(database_url) == expected


def test_alembic_config_preserves_encoded_database_url() -> None:
    database_url = (
        "postgresql://user:encoded%40pass@db.example/app?sslmode=require"
    )
    normalized_url = normalize_database_url(database_url)
    config = Config()
    config.set_main_option(
        "sqlalchemy.url", normalized_url.replace("%", "%%")
    )

    assert config.get_main_option("sqlalchemy.url") == normalized_url
