from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health Check")
def health_check():
    return {
        "status": "healthy",
        "message": "InsightForge AI Backend is running",
    }