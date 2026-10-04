from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    Never hard-code secrets or credentials directly in the codebase.
    """
    APP_NAME: str = "GeoIntelligence AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database configuration (defaults to local SQLite, easily overridden with PostgreSQL DATABASE_URL)
    DATABASE_URL: str = "sqlite:///./geointelligence.db"

    # API Keys & Secrets for External Data Ingestion
    EIA_API_KEY: Optional[str] = None
    ACLED_API_KEY: Optional[str] = None
    ACLED_ACCESS_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
