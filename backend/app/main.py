import logging

from fastapi import FastAPI
from fastapi import Request
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from fastapi.responses import JSONResponse

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)

@app.on_event("startup")
async def startup_event():
    logger.info("InsightForge AI Backend started successfully.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )

@app.get("/")
def root():
    return {
        "message": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)