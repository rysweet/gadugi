"""
Configuration for event-router.
"""

import os
from typing import Optional, Any, List

# Try to import from pydantic_settings (newer version) or fall back to pydantic
try:
    from pydantic_settings import BaseSettings  # type: ignore[import-untyped]
    from pydantic import Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    try:
        from pydantic import BaseSettings, Field  # type: ignore[import-untyped]
        PYDANTIC_AVAILABLE = True
    except ImportError:
        # Fallback for older versions
        from typing import Any
        PYDANTIC_AVAILABLE = False
        BaseSettings = object  # type: ignore[misc]
        def Field(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
            return default


class Settings(BaseSettings):  # type: ignore
    """Enhanced application settings with memory system integration."""

    # Service configuration
    service_name: str = Field(default="event-router", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")

    # Server configuration - respects environment variables
    host: str = Field(default="0.0.0.0", description="Server host", env="EVENT_ROUTER_HOST")
    port: int = Field(default=8000, description="Server port", env="EVENT_ROUTER_PORT")
    debug: bool = Field(default=False, description="Debug mode")

    # Memory System Configuration
    memory_backend_url: str = Field(
        default="http://localhost:8000",
        description="URL for memory system MCP backend"
    )
    sqlite_db_path: str = Field(
        default=".claude/data/events.db",
        description="Path to SQLite database for event storage"
    )
    enable_memory_integration: bool = Field(
        default=True,
        description="Enable integration with Gadugi memory system"
    )

    # Event System Configuration
    max_event_cache_size: int = Field(
        default=1000,
        description="Maximum number of events to cache in memory"
    )
    event_retention_days: int = Field(
        default=30,
        description="Number of days to retain events in storage"
    )
    high_priority_events_to_memory: bool = Field(
        default=True,
        description="Store high/critical priority events in memory system"
    )

    # Event Replay Configuration
    max_replay_events: int = Field(
        default=5000,
        description="Maximum number of events to replay in a single request"
    )
    replay_timeout_seconds: int = Field(
        default=300,
        description="Timeout for event replay operations"
    )

    # Event Filtering Configuration
    filter_cache_ttl_minutes: int = Field(
        default=5,
        description="TTL for filter result cache in minutes"
    )
    max_filter_results: int = Field(
        default=1000,
        description="Maximum number of events to return from filter"
    )

    # Database configuration (legacy)
    database_url: Optional[str] = Field(default=None, description="Database URL (legacy)")

    # Redis configuration (for future use)
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching")
    enable_redis_cache: bool = Field(default=False, description="Enable Redis caching")

    # Logging configuration
    log_level: str = Field(default="INFO", description="Log level")
    log_file: Optional[str] = Field(
        default=".claude/logs/event-router.log",
        description="Log file path"
    )
    enable_structured_logging: bool = Field(
        default=True,
        description="Enable structured JSON logging"
    )

    # Security configuration
    api_key: Optional[str] = Field(default=None, description="API Key for authentication")
    secret_key: str = Field(default="change-me-in-production", description="Secret key")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )

    # Health Check Configuration
    health_check_interval_seconds: int = Field(
        default=60,
        description="Interval for automatic health checks"
    )
    memory_health_check_enabled: bool = Field(
        default=True,
        description="Enable memory system health checks"
    )

    # Performance Configuration
    async_workers: int = Field(
        default=4,
        description="Number of async workers for event processing"
    )
    batch_size: int = Field(
        default=100,
        description="Batch size for bulk operations"
    )

    class Config:
        """Pydantic config."""
        env_prefix = "EVENT_ROUTER_"
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    if PYDANTIC_AVAILABLE:
        return Settings()  # type: ignore
    else:
        # Create a simple settings object with defaults when pydantic is not available
        settings = Settings()  # type: ignore
        settings.service_name = "event-router"
        settings.service_version = "1.0.0"
        settings.host = os.environ.get("EVENT_ROUTER_HOST", "0.0.0.0")
        settings.port = int(os.environ.get("EVENT_ROUTER_PORT", "8000"))
        settings.debug = os.environ.get("DEBUG", "False").lower() == "true"
        settings.memory_backend_url = "http://localhost:8000"
        settings.sqlite_db_path = ".claude/data/events.db"
        settings.enable_memory_integration = True
        settings.max_event_cache_size = 1000
        settings.event_retention_days = 30
        settings.high_priority_events_to_memory = True
        settings.max_replay_events = 5000
        settings.replay_timeout_seconds = 300
        settings.filter_cache_ttl_minutes = 5
        settings.max_filter_results = 1000
        settings.database_url = None
        settings.redis_url = None
        settings.enable_redis_cache = False
        settings.log_level = "INFO"
        settings.log_file = ".claude/logs/event-router.log"
        settings.enable_structured_logging = True
        settings.api_key = None
        settings.secret_key = "change-me-in-production"
        settings.cors_origins = ["http://localhost:3000", "http://localhost:8080"]
        settings.health_check_interval_seconds = 60
        settings.memory_health_check_enabled = True
        settings.async_workers = 4
        settings.batch_size = 100
        return settings


# Flask-specific config class
class Config:
    """Enhanced Flask configuration with production settings."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    JSON_SORT_KEYS: bool = False
    JSONIFY_PRETTYPRINT_REGULAR: bool = True

    # Event Router specific Flask settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max request size
    JSONIFY_MIMETYPE: str = 'application/json'

    # CORS Configuration
    CORS_ORIGINS: str = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:8080'
    )

    # Request timeout
    TIMEOUT: int = int(os.environ.get('TIMEOUT', 300))  # 5 minutes default


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    EVENT_ROUTER_LOG_LEVEL = "DEBUG"
    EVENT_ROUTER_ENABLE_MEMORY_INTEGRATION = True
    EVENT_ROUTER_SQLITE_DB_PATH = ".claude/data/events_dev.db"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    EVENT_ROUTER_LOG_LEVEL = "INFO"
    EVENT_ROUTER_ENABLE_STRUCTURED_LOGGING = True
    EVENT_ROUTER_MEMORY_HEALTH_CHECK_ENABLED = True
    EVENT_ROUTER_SQLITE_DB_PATH = "/var/lib/claude/events.db"

    # Production security settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    EVENT_ROUTER_SQLITE_DB_PATH = ":memory:"  # In-memory for tests
    EVENT_ROUTER_ENABLE_MEMORY_INTEGRATION = False  # Disable for unit tests
