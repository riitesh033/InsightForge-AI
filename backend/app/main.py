import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.api import api_router
from app.core.config import settings
from app.db.database import SessionLocal, ensure_migrations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle.

    On startup we verify the database is reachable and (for a fresh database)
    bootstrap the schema via Alembic so ``docker compose up`` works end-to-end
    without a manual migration step.
    """
    try:
        ensure_migrations()
    except Exception:  # pragma: no cover - logged, surfaced by /health/db
        logger.exception("Database migration bootstrap failed at startup")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to InsightForge AI API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get(f"{settings.API_V1_STR}/health/db")
def health_db():
    """Prove Python -> SQLAlchemy -> PostgreSQL connectivity."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        logger.exception("Database health check failed")
        return {"status": "error", "database": "unavailable"}
