"""
Application configuration via environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://wms:wms@localhost:5432/wms_dev"
    SYNC_DATABASE_URL: str = "postgresql://wms:wms@localhost:5432/wms_dev"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None  # Defaults to REDIS_URL in celery_app

    # JWT
    JWT_SECRET_KEY: str = "change-me-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    APP_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]  # Restrict in production

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
