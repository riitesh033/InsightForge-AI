from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import health

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)