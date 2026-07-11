from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "InsightForge AI"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
    env_file=".env",
    case_sensitive=True,
    extra="ignore",
)



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()