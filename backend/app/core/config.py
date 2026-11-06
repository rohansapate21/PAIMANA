"""
SIH 2026 — PS26103 | Application Configuration
==============================================
Loads environment variables and application settings via Pydantic Settings.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "PAIMANA Predictive Analytics & Early Warning System"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"

    # Security & JWT
    SECRET_KEY: str = "paimana_secure_jwt_secret_key_sih2026_mospi"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "sih2026_paimana"
    POSTGRES_USER: str = "paimana_admin"
    POSTGRES_PASSWORD: str = "changeme_in_production"
    DATABASE_URL: Optional[str] = None

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    # MLflow
    MLFLOW_TRACKING_URI: str = "sqlite:///mlflow.db"
    MLFLOW_EXPERIMENT_NAME: str = "sih2026-paimana-risk"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

