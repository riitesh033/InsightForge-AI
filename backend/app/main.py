from fastapi import FastAPI
from app.api.v1.health import router as health_router

app = FastAPI(
    title="InsightForge AI API",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": "Welcome to InsightForge AI API",
        "docs": "/docs",
    }

app.include_router(health_router, prefix="/api/v1")