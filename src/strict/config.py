"""Rough Configuration - Pydantic Settings.

This module handles environment-based configuration using Pydantic Settings.
All configuration is validated at startup and immutable thereafter.

Usage:
    from strict.config import settings
    print(settings.secret_key)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StrictSettings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are validated at instantiation time.
    Uses the STRICT_ prefix for all environment variables.

    Environment Variables:
        STRICT_SECRET_KEY: Secret key for cryptographic operations
        STRICT_DEBUG: Enable debug mode (default: False)
        STRICT_LOG_LEVEL: Logging level (default: INFO)
        STRICT_MAX_RETRIES: Maximum retry attempts (default: 3)
        STRICT_TIMEOUT_SECONDS: Default timeout in seconds (default: 30.0)
        STRICT_CLOUD_ENDPOINT: Cloud processor endpoint URL
        STRICT_LOCAL_MODEL_PATH: Path to local model files
        STRICT_TOKEN_THRESHOLD: Threshold for processor routing (default: 500)
    """

    model_config = SettingsConfigDict(
        env_prefix="STRICT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,
    )

    # Security
    secret_key: SecretStr = Field(
        default=SecretStr(""),
        description="Secret key for cryptographic operations. User to fill.",
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API Key",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama Base URL",
    )

    # Persistence Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/strict_db",
        description="PostgreSQL Connection URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis Connection URL",
    )
    s3_endpoint_url: str | None = Field(
        default=None,
        description="S3 Endpoint URL (for MinIO/AWS)",
    )
    s3_access_key: SecretStr | None = Field(
        default=None,
        description="S3 Access Key",
    )
    s3_secret_key: SecretStr | None = Field(
        default=None,
        description="S3 Secret Key",
    )
    s3_bucket_name: str = Field(
        default="strict-storage",
        description="S3 Bucket Name",
    )

    # Runtime Configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: str = Field(
        default="INFO",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level",
    )

    # Processing Configuration
    max_retries: Annotated[int, Field(ge=0, le=10)] = Field(
        default=3,
        description="Maximum retry attempts on failure",
    )
    timeout_seconds: Annotated[float, Field(gt=0, le=300)] = Field(
        default=30.0,
        description="Default timeout in seconds",
    )

    # Processor Configuration
    cloud_endpoint: str = Field(
        default="",
        description="Cloud processor endpoint URL",
    )
    local_model_path: str = Field(
        default="",
        description="Path to local model files",
    )
    token_threshold: Annotated[int, Field(gt=0, le=100000)] = Field(
        default=500,
        description="Token threshold for processor routing",
    )

    # Failover Configuration
    cloud_failure_probability: Annotated[float, Field(ge=0, le=1)] = Field(
        default=0.01,
        description="Expected cloud failure probability",
    )
    local_failure_probability: Annotated[float, Field(ge=0, le=1)] = Field(
        default=0.05,
        description="Expected local failure probability",
    )
    enable_failover: bool = Field(
        default=True,
        description="Enable automatic failover to local on cloud failure",
    )


@lru_cache
def get_settings() -> StrictSettings:
    """Get cached application settings.

    Settings are loaded once and cached for subsequent calls.
    This ensures configuration is consistent throughout the application.

    Returns:
        StrictSettings instance with validated configuration.
    """
    return StrictSettings()


# Convenience export for direct import
settings = get_settings()
