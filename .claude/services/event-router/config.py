"""
Configuration for event-router.
"""

import os
from typing import Optional
<<<<<<< HEAD
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
=======
from pydantic import BaseSettings


class Settings(BaseSettings):  # type: ignore
>>>>>>> feature/gadugi-v0.3-regeneration
    """Application settings."""

    # Service configuration
    service_name: str = "event-router"
    service_version: str = "0.1.0"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Database configuration (if needed)
    database_url: Optional[str] = None

    # Redis configuration (if needed)
    redis_url: Optional[str] = None

    # Logging configuration
    log_level: str = "INFO"

    # Security configuration
    api_key: Optional[str] = None
    secret_key: str = "change-me-in-production"

<<<<<<< HEAD
    model_config = {
        "env_prefix": "EVENT_ROUTER_",
        "env_file": ".env"
    }
=======
    class Config:
        env_prefix = "EVENT-ROUTER_"
        env_file = ".env"
>>>>>>> feature/gadugi-v0.3-regeneration


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Flask-specific config class
class Config:
    """Flask configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
