import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api import api_router
from app.core.config import settings
from app.db.database import ensure_migrations
from app.services.cloud_storage import supabase_storage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle.

    On startup we verify the database is reachable and (for a fresh database)
    bootstrap the schema via Alembic so ``docker compose up`` works end-to-end
    without a manual migration step. Configuration that cannot work in
    production is reported loudly here instead of failing at request time.
    """

    try:
        ensure_migrations()
    except Exception:
        logger.exception("Database migration failed at startup")
        raise

    if settings.USE_CLOUD_STORAGE:
        if not supabase_storage.is_configured():
            logger.error(
                "Cloud storage is enabled but Supabase is not configured. "
                "Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and "
                "SUPABASE_BUCKET, or disable USE_CLOUD_STORAGE."
            )
    elif not settings.is_development:
        logger.warning(
            "Cloud storage is disabled in a non-development environment. "
            "Uploaded datasets will only exist on the local filesystem and "
            "will be lost when the container is replaced. Configure Supabase "
            "and leave USE_CLOUD_STORAGE unset (or true) for persistence."
        )

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe JSON 500 for unexpected failures.

    FastAPI handles this inside the middleware stack, so the response still
    travels back out through ``CORSMiddleware`` and carries the CORS headers.
    Letting the exception escape instead produces a bare server error with no
    CORS headers, which browsers surface as a misleading CORS failure rather
    than the real server-side problem.
    """

    logger.exception(
        "Unhandled error while processing %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                "An unexpected server error occurred. "
                "Please try again."
            )
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    # The dataset and report downloads are named from this header, which the
    # browser hides from JavaScript unless the server exposes it.
    expose_headers=["Content-Disposition"],
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
