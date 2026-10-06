from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root:
# backend/
BASE_DIR = Path(__file__).resolve().parents[2]

# Explicitly load backend/.env
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # ============================================================
    # Project
    # ============================================================

    PROJECT_NAME: str = "InsightForge AI"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # One or more browser origins, comma separated.
    # Example: https://app.example.com,https://staging.example.com
    FRONTEND_URL: str = "http://localhost:5173"

    # ============================================================
    # Local Storage
    # ============================================================

    DATASET_STORAGE_DIR: str = "app/uploads/datasets"
    STUDENT_VERIFICATION_STORAGE_DIR: str = (
        "private_uploads/student_verification"
    )

    # ============================================================
    # Cloud Storage - Supabase
    # ============================================================

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET: str = "insightforge-files"

    # Keep each uploaded cloud-storage chunk below
    # Supabase's per-file size limit.
    SUPABASE_CHUNK_SIZE_MB: int = 40

    # Persist datasets in Supabase Storage.
    #
    # Leaving this unset auto-detects: cloud storage is enabled whenever
    # the Supabase credentials and bucket are present. That keeps uploads
    # alive across container restarts on hosts with an ephemeral
    # filesystem (such as Render). Set it explicitly to "false" to force
    # local-only storage during development.
    USE_CLOUD_STORAGE: bool = False

    # ============================================================
    # Google OAuth
    # ============================================================

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_CALLBACK_URL: str = ""

    # ============================================================
    # Email / Brevo
    # ============================================================

    BREVO_API_KEY: str = ""

    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "InsightForge AI"

    # Legacy SMTP settings kept for compatibility.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    SUPPORT_EMAIL: str = "support@insightforge.ai"
    BUSINESS_NAME: str = "InsightForge AI"
    BUSINESS_ADDRESS: str = ""

    # ============================================================
    # Payments - Stripe
    # ============================================================

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_BUSINESS: str = ""

    # ============================================================
    # AI Provider
    # ============================================================

    # gemini -> openrouter -> ollama
    AI_PROVIDER: str = "gemini"

    # ============================================================
    # Gemini
    # ============================================================

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ============================================================
    # OpenRouter
    # ============================================================

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/auto"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ============================================================
    # Ollama
    # ============================================================

    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "qwen3:8b"

    # ============================================================
    # Pydantic Settings Configuration
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("FRONTEND_URL")
    @classmethod
    def _normalize_frontend_url(cls, value: str) -> str:
        """Trim whitespace and trailing slashes from configured origins.

        Browsers send the ``Origin`` header without a trailing slash, so a
        configured value such as ``https://app.example.com/`` would never
        match and every cross-origin request would fail.
        """

        origins = [
            origin.strip().rstrip("/")
            for origin in value.split(",")
            if origin.strip()
        ]

        return ",".join(origins)

    @model_validator(mode="after")
    def _default_cloud_storage(self) -> "Settings":
        """Enable cloud storage when Supabase is configured but unset.

        ``USE_CLOUD_STORAGE`` distinguishes three deployments:

        * explicitly ``true``  -> always store datasets in Supabase
        * explicitly ``false`` -> always store datasets locally
        * unset                -> store in Supabase when it is configured
        """

        if (
            "USE_CLOUD_STORAGE" not in self.model_fields_set
            and self.SUPABASE_URL
            and self.SUPABASE_SERVICE_ROLE_KEY
            and self.SUPABASE_BUCKET
        ):
            self.USE_CLOUD_STORAGE = True

        return self

    @property
    def cors_origins(self) -> list[str]:
        """Return the browser origins allowed to call this API."""

        origins = [
            origin
            for origin in self.FRONTEND_URL.split(",")
            if origin
        ]

        return origins or ["http://localhost:5173"]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
