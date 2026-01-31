"""Tests for enhanced error handling."""

import pytest

from strict.errors import (
    AuthenticationError,
    ConfigurationError,
    ErrorCode,
    ProcessingError,
    StrictError,
    StorageError,
    ValidationError,
    create_error_handler,
    handle_pydantic_validation_error,
)
from pydantic import BaseModel, Field


class TestStrictError:
    """Test base StrictError class."""

    def test_error_initialization(self) -> None:
        """Test error initialization."""
        error = StrictError(
            message="Test error",
            code=ErrorCode.VALIDATION_ERROR,
            details={"key": "value"},
        )

        assert error.message == "Test error"
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.details == {"key": "value"}

    def test_error_to_dict(self) -> None:
        """Test converting error to dictionary."""
        error = StrictError(
            message="Test error",
            code=ErrorCode.PROCESSING_ERROR,
            details={"operation": "fft"},
        )

        result = error.to_dict()
        assert result["error"] == "PROCESSING_ERROR"
        assert result["message"] == "Test error"
        assert result["details"] == {"operation": "fft"}

    def test_error_string_representation(self) -> None:
        """Test error string representation."""
        error = StrictError(
            message="Test error",
            code=ErrorCode.STORAGE_ERROR,
        )

        assert str(error) == "[STORAGE_ERROR] Test error"

    def test_error_with_details_string(self) -> None:
        """Test error string with details."""
        error = StrictError(
            message="Test error",
            code=ErrorCode.VALIDATION_ERROR,
            details={"field": "email"},
        )

        assert "field" in str(error)
        assert "email" in str(error)


class TestValidationError:
    """Test ValidationError subclass."""

    def test_validation_error_with_field(self) -> None:
        """Test ValidationError with field information."""
        error = ValidationError(
            message="Invalid email format",
            field="email",
            value="not-an-email",
        )

        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "email"
        assert error.details["value"] == "not-an-email"

    def test_validation_error_without_field(self) -> None:
        """Test ValidationError without field."""
        error = ValidationError(message="Generic validation error")

        assert "field" not in error.details


class TestProcessingError:
    """Test ProcessingError subclass."""

    def test_processing_error_with_operation(self) -> None:
        """Test ProcessingError with operation."""
        error = ProcessingError(
            message="FFT failed",
            operation="fft",
            input_data=[1, 2, 3],
        )

        assert error.code == ErrorCode.PROCESSING_ERROR
        assert error.details["operation"] == "fft"
        assert "input" in error.details


class TestStorageError:
    """Test StorageError subclass."""

    def test_storage_error_with_resource(self) -> None:
        """Test StorageError with resource information."""
        error = StorageError(
            message="Database connection failed",
            operation="connect",
            resource="postgresql",
        )

        assert error.code == ErrorCode.STORAGE_ERROR
        assert error.details["operation"] == "connect"
        assert error.details["resource"] == "postgresql"


class TestAuthenticationError:
    """Test AuthenticationError subclass."""

    def test_authentication_error_defaults(self) -> None:
        """Test AuthenticationError default message."""
        error = AuthenticationError()

        assert error.code == ErrorCode.AUTH_ERROR
        assert error.message == "Authentication failed"

    def test_authentication_error_with_user(self) -> None:
        """Test AuthenticationError with user ID."""
        error = AuthenticationError(
            message="Invalid token",
            user_id="user123",
        )

        assert error.details["user_id"] == "user123"


class TestConfigurationError:
    """Test ConfigurationError subclass."""

    def test_configuration_error_with_setting(self) -> None:
        """Test ConfigurationError with setting name."""
        error = ConfigurationError(
            message="Missing required configuration",
            setting="DATABASE_URL",
        )

        assert error.code == ErrorCode.CONFIG_ERROR
        assert error.details["setting"] == "DATABASE_URL"


class TestPydanticErrorHandling:
    """Test Pydantic error conversion."""

    def test_handle_pydantic_validation_error(self) -> None:
        """Test converting Pydantic ValidationError."""

        class TestModel(BaseModel):
            email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")

        try:
            TestModel(email="invalid-email")
            pytest.fail("Should have raised ValidationError")
        except Exception as e:
            strict_error = handle_pydantic_validation_error(e)
            assert isinstance(strict_error, ValidationError)
            assert strict_error.code == ErrorCode.VALIDATION_ERROR
            assert "errors" in strict_error.details


class TestErrorHandler:
    """Test error handler creation."""

    def test_default_error_handler(self) -> None:
        """Test default error handler mappings."""
        handler = create_error_handler()

        # ValueError maps to ValidationError
        error = handler(ValueError("Invalid input"))
        assert isinstance(error, ValidationError)

        # KeyError maps to StorageError
        error = handler(KeyError("missing_key"))
        assert isinstance(error, StorageError)

    def test_custom_error_handler(self) -> None:
        """Test custom error handler mappings."""
        handler = create_error_handler(
            {
                RuntimeError: ProcessingError,
            }
        )

        error = handler(RuntimeError("Processing failed"))
        assert isinstance(error, ProcessingError)

    def test_unmapped_error(self) -> None:
        """Test handling of unmapped exception types."""
        handler = create_error_handler()

        error = handler(RuntimeError("Unknown error"))
        assert isinstance(error, StrictError)
        assert error.code == ErrorCode.INTERNAL_ERROR

    def test_error_handler_preserves_original(self) -> None:
        """Test that original exception is preserved."""
        handler = create_error_handler()
        original_error = ValueError("test")

        strict_error = handler(original_error)
        assert strict_error.original_error is original_error
