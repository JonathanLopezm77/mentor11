"""
app/core/config.py
Configuración central del proyecto. Lee variables desde .env automáticamente.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # ── Proyecto ──────────────────────────────────────
    PROJECT_NAME: str = "Mentor 11"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ── Base de datos ─────────────────────────────────
    DATABASE_URL: str
    DATABASE_URL_SYNC: str = ""

    # Railway provee DATABASE_URL como postgresql://, lo convertimos al driver correcto
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_async_url(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def fix_sync_url(cls, v: str) -> str:
        if not v:
            return ""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # ── Seguridad / JWT ───────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── CORS ──────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # ── Email ─────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@mentor11.com"

    # ── IA (Premium) ──────────────────────────────────
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Permite que ALLOWED_ORIGINS se lea como lista separada por comas
        # desde el .env: ALLOWED_ORIGINS=http://a.com,http://b.com
        extra = "ignore"


# Instancia global — importar desde aquí en todo el proyecto
settings = Settings()
