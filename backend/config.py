"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Cache TTL (seconds)
    CACHE_TTL_CRYPTO: int
    CACHE_TTL_OTHER: int

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int

    # CORS
    CORS_ORIGINS: list[str]

    # ML
    ML_ENABLED: bool
    ML_MODEL_PATH: str

    # Server
    HOST: str
    PORT: int

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
