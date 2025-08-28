"""
Configuration for event-router.
"""

import os
from typing import Optional, Any

# Try to import from pydantic_settings (newer version) or fall back to pydantic
try:
    from pydantic_settings import BaseSettings  # type: ignore[import-untyped]
    from pydantic import Field
except ImportError:
    try:
        from pydantic import BaseSettings, Field  # type: ignore[import-untyped]
    except ImportError:
        # Fallback for older versions
        from typing import Any
        BaseSettings = object  # type: ignore[misc]
        def Field(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
            return None


class Settings(BaseSettings):  # type: ignore
    """Application settings."""

    # Service configuration
    service_name: str = Field(default="event-router", description="Service name")
    service_version: str = Field(default="0.1.0", description="Service version")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Database configuration (if needed)
    database_url: Optional[str] = Field(default=None, description="Database URL")

    # Redis configuration (if needed)
    redis_url: Optional[str] = Field(default=None, description="Redis URL")

    # Logging configuration
    log_level: str = Field(default="INFO", description="Log level")

    # Security configuration
    api_key: Optional[str] = Field(default=None, description="API Key")
    secret_key: str = Field(default="change-me-in-production", description="Secret key")

    class Config:
        """Pydantic config."""
        env_prefix = "EVENT_ROUTER_"
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()  # type: ignore


# Flask-specific config class
class Config:
    """Flask configuration."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    JSON_SORT_KEYS: bool = False
    JSONIFY_PRETTYPRINT_REGULAR: bool = True