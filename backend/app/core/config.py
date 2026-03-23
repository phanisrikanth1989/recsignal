from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    # App
    APP_NAME: str = "RecSignal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Database (SQLite for local dev, can swap to Oracle/Postgres later)
    DATABASE_URL: str = "sqlite:///./recsignal.db"

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "recsignal@example.com"
    SMTP_USE_TLS: bool = True

    # Security
    AGENT_API_KEY: str = "sample-secret-key"
    SECRET_KEY: str = "recsignal-dev-secret-change-in-prod"

    # Monitoring
    STALE_THRESHOLD_MINUTES: int = 20

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
