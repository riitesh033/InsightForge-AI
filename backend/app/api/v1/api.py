from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import health
from app.api.v1.endpoints import users

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)