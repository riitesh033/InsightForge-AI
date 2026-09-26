import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", summary="Health Check")
@router.get("/", summary="Health Check", include_in_schema=False)
def health_check():
    return {
        "status": "healthy",
        "message": "InsightForge AI Backend is running",
    }


@router.get("/db", summary="Database Health Check")
def database_health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from None

    return {"status": "ok", "database": "connected"}