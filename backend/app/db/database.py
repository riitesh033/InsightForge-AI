"""Database engine / session configuration and process-wide Alembic upgrade."""

import logging
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def normalize_database_url(database_url: str) -> str:
    """Select the installed psycopg2 driver for generic PostgreSQL URLs."""
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + database_url[len("postgresql://"):]
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg2://" + database_url[len("postgres://"):]
    return database_url


engine = create_engine(
    normalize_database_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def run_migrations() -> None:
    """Apply all pending Alembic revisions (idempotent)."""
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    alembic_url = normalize_database_url(settings.DATABASE_URL).replace("%", "%%")
    cfg.set_main_option("sqlalchemy.url", alembic_url)
    command.upgrade(cfg, "head")
    logger.info("Database migrations are at Alembic head.")


_migration_lock = threading.Lock()
_migrations_done = False


def ensure_migrations() -> None:
    """Thread-safe, once-per-process wrapper around :func:`run_migrations`."""
    global _migrations_done
    with _migration_lock:
        if _migrations_done:
            return
        run_migrations()
        _migrations_done = True


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
