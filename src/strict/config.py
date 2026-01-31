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

from pydantic import Field, SecretStr, model_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default hash for "secret"
_DEFAULT_ADMIN_HASH = "$2b$12$npx34fPjj96wXPYvVp4Eg.AkSJPSZr6clNxacAt.LiaDWAfzV518m"


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
        default="",
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

    # Auth Configuration
    auth_secret_key: SecretStr = Field(
        default=SecretStr(""),
        description="Secret key for JWT (required in production)",
    )
    valid_api_keys: list[SecretStr] = Field(
        default_factory=list,
        description="List of valid API keys for authentication",
    )
    admin_username: str = Field(
        default="admin",
        description="Administrator username",
    )
    admin_password_hash: str = Field(
        default="$2b$12$npx34fPjj96wXPYvVp4Eg.AkSJPSZr6clNxacAt.LiaDWAfzV518m",
        description="Administrator password hash (bcrypt)",
    )
    auth_algorithm: str = Field(
        default="HS256",
        description="JWT Algorithm",
    )
    auth_access_token_expire_minutes: int = Field(
        default=30,
        description="Token expiration time",
    )

    # CORS Configuration
    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins for production",
    )
    cors_allow_credentials: bool = Field(
        default=False,
        description="Allow credentials in CORS requests",
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

    @model_validator(mode="after")
    def validate_security_in_production(self) -> "StrictSettings":
        """Ensure secure defaults in production."""
        # Check if auth_secret_key is set
        if not self.auth_secret_key.get_secret_value():
            if not self.debug:
                raise ValueError(
                    "auth_secret_key must be set in production. "
                    "Set STRICT_AUTH_SECRET_KEY environment variable."
                )
            # In debug mode, provide a default for development
            object.__setattr__(
                self,
                "auth_secret_key",
                SecretStr("dev-secret-key-do-not-use-in-production"),
            )

        # Check database_url in non-debug mode
        if not self.debug and not self.database_url:
            raise ValueError(
                "database_url must be set in production. "
                "Set STRICT_DATABASE_URL environment variable."
            )

        # Ensure default admin password hash is not used in production
        if not self.debug and self.admin_password_hash == _DEFAULT_ADMIN_HASH:
            raise ValueError(
                "Default administrator password hash detected. "
                "You must set a custom STRICT_ADMIN_PASSWORD_HASH in production."
            )

        return self


@lru_cache
def get_settings() -> StrictSettings:
    """Get cached application settings.

    Settings are loaded once and cached for subsequent calls.
    This ensures configuration is consistent throughout the application.

    Returns:
        StrictSettings instance with validated configuration.
    """
    try:
        return StrictSettings()
    except ValidationError as e:
        # Configuration validation failed - this is critical
        import warnings
        import sys

        error_msg = f"Configuration validation failed: {e}"
        warnings.warn(error_msg, stacklevel=2)

        # In debug mode, provide helpful development defaults
        import os

        if os.getenv("STRICT_DEBUG", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "y",
            "on",
        ):
            warnings.warn(
                "Using DEBUG MODE with insecure defaults - NOT FOR PRODUCTION",
                stacklevel=2,
            )
            return StrictSettings(
                debug=True,
                auth_secret_key=SecretStr("dev-secret-key-do-not-use-in-production"),
                database_url="",
                redis_url="redis://localhost:6379/0",
            )

        # In production, fail fast
        sys.exit(1)
    except Exception as e:
        # Unexpected error - log details and exit
        import warnings
        import sys

        error_msg = f"Failed to load settings: {type(e).__name__}: {e}"
        warnings.warn(error_msg, stacklevel=2)
        sys.exit(1)


# Convenience export for direct import
settings = get_settings()
