import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.db.database import ensure_migrations

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
    except Exception:
        logger.exception("Database migration failed at startup")
        raise

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
