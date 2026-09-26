"""Database engine / session configuration and process-wide Alembic upgrade."""

import logging
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
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
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
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
