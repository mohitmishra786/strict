"""Enhanced Error Handling for Strict.

Provides custom exceptions and error handlers for better error management.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError as PydanticValidationError

if TYPE_CHECKING:
    from collections.abc import Callable


class ErrorCode(str, Enum):
    """Standard error codes for Strict application."""

    # Validation Errors (1xxx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # Processing Errors (2xxx)
    PROCESSING_ERROR = "PROCESSING_ERROR"
    COMPUTATION_ERROR = "COMPUTATION_ERROR"
    SIGNAL_ERROR = "SIGNAL_ERROR"
    MATH_ERROR = "MATH_ERROR"

    # Storage Errors (3xxx)
    STORAGE_ERROR = "STORAGE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

    # Authentication Errors (4xxx)
    AUTH_ERROR = "AUTH_ERROR"
    TOKEN_ERROR = "TOKEN_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # External Service Errors (5xxx)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    LLM_ERROR = "LLM_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"

    # Configuration Errors (6xxx)
    CONFIG_ERROR = "CONFIG_ERROR"
    MISSING_ENV_VAR = "MISSING_ENV_VAR"

    # General Errors (9xxx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class StrictError(Exception):
    """Base exception for all Strict errors.

    Provides structured error information with error codes and context.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize StrictError.

        Args:
            message: Human-readable error message.
            code: Error code from ErrorCode enum.
            details: Additional error context.
            original_error: Original exception that caused this error.
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """String representation of error."""
        if self.details:
            return f"[{self.code.value}] {self.message}: {self.details}"
        return f"[{self.code.value}] {self.message}"


class ValidationError(StrictError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Validation error message.
            field: Field that failed validation.
            value: Value that failed validation.
            details: Additional error details.
            original_error: Original exception.
        """
        final_details = details or {}
        if field:
            final_details["field"] = field
        if value is not None:
            final_details["value"] = str(value)

        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            details=final_details,
            original_error=original_error,
        )


class ProcessingError(StrictError):
    """Raised when signal or math processing fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        input_data: Any = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize ProcessingError.

        Args:
            message: Error message.
            operation: Operation that failed.
            input_data: Input that caused the error.
            details: Additional error details.
            original_error: Original exception.
        """
        final_details = details or {}
        if operation:
            final_details["operation"] = operation
        if input_data is not None:
            final_details["input"] = str(input_data)[:100]  # Truncate large inputs

        super().__init__(
            message=message,
            code=ErrorCode.PROCESSING_ERROR,
            details=final_details,
            original_error=original_error,
        )


class StorageError(StrictError):
    """Raised when storage operations fail."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        resource: str | None = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize StorageError.

        Args:
            message: Error message.
            operation: Operation that failed (read/write/delete).
            resource: Resource being accessed.
            details: Additional error details.
            original_error: Original exception.
        """
        final_details = details or {}
        if operation:
            final_details["operation"] = operation
        if resource:
            final_details["resource"] = resource

        super().__init__(
            message=message,
            code=ErrorCode.STORAGE_ERROR,
            details=final_details,
            original_error=original_error,
        )


class AuthenticationError(StrictError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message.
            user_id: User ID that failed authentication.
            details: Additional error details.
            original_error: Original exception.
        """
        final_details = details or {}
        if user_id:
            final_details["user_id"] = user_id

        super().__init__(
            message=message,
            code=ErrorCode.AUTH_ERROR,
            details=final_details,
            original_error=original_error,
        )


class ConfigurationError(StrictError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        setting: str | None = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize ConfigurationError.

        Args:
            message: Error message.
            setting: Configuration setting that is invalid.
            details: Additional error details.
            original_error: Original exception.
        """
        final_details = details or {}
        if setting:
            final_details["setting"] = setting

        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_ERROR,
            details=final_details,
            original_error=original_error,
        )


def handle_pydantic_validation_error(error: PydanticValidationError) -> ValidationError:
    """Convert Pydantic ValidationError to Strict ValidationError.

    Args:
        error: Pydantic ValidationError.

    Returns:
        Strict ValidationError with details.
    """
    errors_list = []
    for err in error.errors():
        loc = " -> ".join(str(l) for l in err["loc"])
        errors_list.append(f"{loc}: {err['msg']}")

    return ValidationError(
        message="Validation failed",
        details={"errors": errors_list},
        original_error=error,
    )


def create_error_handler(
    error_map: dict[type[Exception], type[StrictError]] | None = None,
) -> Callable[[Exception], StrictError]:
    """Create an error handler function.

    Args:
        error_map: Mapping from exception types to Strict error types.

    Returns:
        Error handler function.

    Example:
        handler = create_error_handler({
            ValueError: ValidationError,
            KeyError: StorageError,
        })
        try:
            risky_operation()
        except Exception as e:
            strict_error = handler(e)
            logger.error(str(strict_error))
    """
    default_map: dict[type[Exception], type[StrictError]] = {
        ValueError: ValidationError,
        KeyError: StorageError,
        PermissionError: AuthenticationError,
    }

    if error_map:
        default_map.update(error_map)

    def handler(exc: Exception) -> StrictError:
        """Handle exception and convert to StrictError."""
        for exc_type, strict_error_type in default_map.items():
            if isinstance(exc, exc_type):
                return strict_error_type(
                    message=str(exc),
                    original_error=exc,
                )

        # Default fallback
        return StrictError(
            message=str(exc),
            code=ErrorCode.INTERNAL_ERROR,
            original_error=exc,
        )

    return handler
