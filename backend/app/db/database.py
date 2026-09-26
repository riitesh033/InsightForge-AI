"""Database engine / session configuration.

Includes a best-effort, process-wide Alembic bootstrap so that the FastAPI
application can start against an empty database (used by ``docker compose up``
and first-run local development). Alembic itself remains the source of truth;
this only runs ``upgrade head`` once per process when the schema is missing.
"""

import logging
import threading

from sqlalchemy import create_engine, inspect
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
    """Run ``alembic upgrade head`` programmatically (idempotent)."""
    from alembic import command
    from alembic.config import Config

    bind = engine.connect()
    try:
        existing = set(inspect(bind).get_table_names())
    finally:
        bind.close()

    if "alembic_version" in existing:
        logger.info("Database already under Alembic management; skipping bootstrap.")
        return

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(cfg, "head")
    logger.info("Alembic bootstrap: database upgraded to head.")


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
