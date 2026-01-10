"""Vaak Configuration - Pydantic Settings.

This module handles environment-based configuration using Pydantic Settings.
All configuration is validated at startup and immutable thereafter.

Usage:
    from vaak.config import settings
    print(settings.secret_key)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VaakSettings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are validated at instantiation time.
    Uses the VAAK_ prefix for all environment variables.

    Environment Variables:
        VAAK_SECRET_KEY: Secret key for cryptographic operations
        VAAK_DEBUG: Enable debug mode (default: False)
        VAAK_LOG_LEVEL: Logging level (default: INFO)
        VAAK_MAX_RETRIES: Maximum retry attempts (default: 3)
        VAAK_TIMEOUT_SECONDS: Default timeout in seconds (default: 30.0)
        VAAK_CLOUD_ENDPOINT: Cloud processor endpoint URL
        VAAK_LOCAL_MODEL_PATH: Path to local model files
        VAAK_TOKEN_THRESHOLD: Threshold for processor routing (default: 500)
    """

    model_config = SettingsConfigDict(
        env_prefix="VAAK_",
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
def get_settings() -> VaakSettings:
    """Get cached application settings.

    Settings are loaded once and cached for subsequent calls.
    This ensures configuration is consistent throughout the application.

    Returns:
        VaakSettings instance with validated configuration.
    """
    return VaakSettings()


# Convenience export for direct import
settings = get_settings()
