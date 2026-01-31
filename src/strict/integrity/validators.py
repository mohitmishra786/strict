"""Reusable Validator Logic.

This module contains reusable validation functions and utilities
that can be composed into Pydantic validators.

These are pure functions - no side effects, no I/O.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from strict.integrity.schemas import FeatureSchema


# -----------------------------------------------------------------------------
# Hash Functions
# -----------------------------------------------------------------------------


def compute_input_hash(data: str | bytes) -> str:
    """Compute a SHA-256 hash of the input data.

    Args:
        data: The input data to hash (string or bytes).

    Returns:
        Hexadecimal string representation of the hash.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# -----------------------------------------------------------------------------
# Type Validation Functions
# -----------------------------------------------------------------------------


def is_valid_frequency(value: float) -> bool:
    """Check if a frequency value is physically valid.

    Args:
        value: The frequency value in Hz.

    Returns:
        True if the frequency is positive and finite.
    """
    if not isinstance(value, (int, float)):
        return False
    if value <= 0:
        return False
    if not _is_finite(value):
        return False
    return True


def is_valid_probability(value: float) -> bool:
    """Check if a value is a valid probability.

    Args:
        value: The probability value.

    Returns:
        True if the value is in [0, 1] and finite.
    """
    if not isinstance(value, (int, float)):
        return False
    if not _is_finite(value):
        return False
    return 0 <= value <= 1


def is_valid_amplitude(value: float) -> bool:
    """Check if a value is a valid normalized amplitude.

    Args:
        value: The amplitude value.

    Returns:
        True if the value is in [0, 1) and finite.
    """
    if not isinstance(value, (int, float)):
        return False
    if not _is_finite(value):
        return False
    return 0 <= value < 1


def _is_finite(value: float) -> bool:
    """Check if a float is finite (not inf or nan).

    Args:
        value: The float value to check.

    Returns:
        True if the value is finite.
    """
    import math

    return math.isfinite(value)


# -----------------------------------------------------------------------------
# String Validation Functions
# -----------------------------------------------------------------------------


def is_valid_token_string(value: str, max_length: int = 1_000_000) -> bool:
    """Check if a string is valid for tokenization.

    Args:
        value: The string to validate.
        max_length: Maximum allowed length.

    Returns:
        True if the string is non-empty and within length limits.
    """
    if not isinstance(value, str):
        return False
    if len(value) == 0:
        return False
    if len(value) > max_length:
        return False
    return True


def sanitize_input_string(value: str) -> str:
    """Sanitize input string by removing control characters.

    Keeps printable ASCII, newlines, tabs, and valid UTF-8.

    Args:
        value: The input string to sanitize.

    Returns:
        Sanitized string with control characters removed.
    """
    # Remove ASCII control characters except newline and tab
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return sanitized


# -----------------------------------------------------------------------------
# Cross-Field Validation Functions
# -----------------------------------------------------------------------------


def validate_nyquist_criterion(
    sampling_rate: float, frequency: float
) -> tuple[bool, str]:
    """Validate that sampling rate satisfies Nyquist criterion.

    The sampling rate must be greater than twice the signal frequency
    to avoid aliasing.

    Args:
        sampling_rate: The sampling rate in Hz.
        frequency: The signal frequency in Hz.

    Returns:
        Tuple of (is_valid, error_message).
    """
    nyquist_rate = 2 * frequency
    if sampling_rate <= nyquist_rate:
        return (
            False,
            f"Nyquist criterion violated: sampling_rate ({sampling_rate}) "
            f"must be > 2 * frequency ({nyquist_rate})",
        )
    return (True, "")


def validate_token_processor_compatibility(
    token_count: int, processor_type: str, local_max_tokens: int = 4096
) -> tuple[bool, str]:
    """Validate that the processor can handle the token count.

    Args:
        token_count: Number of tokens in the input.
        processor_type: Type of processor ("cloud", "local", "hybrid").
        local_max_tokens: Maximum tokens for local processor.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if processor_type == "local" and token_count > local_max_tokens:
        return (
            False,
            f"Local processor cannot handle {token_count} tokens. "
            f"Maximum is {local_max_tokens}. Use 'cloud' or 'hybrid' processor_type.",
        )
    return (True, "")


def validate_feature_value(value: Any, schema: FeatureSchema) -> tuple[bool, str]:
    """Validate a single feature value against its schema.

    Args:
        value: The value to validate.
        schema: The FeatureSchema to validate against.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if value is None:
        if schema.required:
            return False, f"Feature '{schema.name}' is required"
        return True, ""

    if schema.feature_type == "numeric":
        # Explicitly reject bools as they are instances of int
        if isinstance(value, bool):
            return (
                False,
                f"Feature '{schema.name}' must be numeric, got bool",
            )
        if not isinstance(value, (int, float)):
            return (
                False,
                f"Feature '{schema.name}' must be numeric, got {type(value).__name__}",
            )
        if schema.min_value is not None and value < schema.min_value:
            return (
                False,
                f"Feature '{schema.name}' value {value} < min_value {schema.min_value}",
            )
        if schema.max_value is not None and value > schema.max_value:
            return (
                False,
                f"Feature '{schema.name}' value {value} > max_value {schema.max_value}",
            )

    elif schema.feature_type == "categorical":
        if schema.allowed_values is not None and value not in schema.allowed_values:
            return (
                False,
                f"Feature '{schema.name}' value '{value}' not in allowed_values {schema.allowed_values}",
            )

    elif schema.feature_type == "boolean":
        if not isinstance(value, bool):
            return (
                False,
                f"Feature '{schema.name}' must be boolean, got {type(value).__name__}",
            )

    elif schema.feature_type == "text":
        if not isinstance(value, str):
            return (
                False,
                f"Feature '{schema.name}' must be string, got {type(value).__name__}",
            )

    return True, ""


# -----------------------------------------------------------------------------
# Error Collection
# -----------------------------------------------------------------------------


def collect_validation_errors(validations: list[tuple[bool, str]]) -> tuple[str, ...]:
    """Collect error messages from a list of validation results.

    Args:
        validations: List of (is_valid, error_message) tuples.

    Returns:
        Tuple of error messages for failed validations.
    """
    return tuple(msg for is_valid, msg in validations if not is_valid and msg)


def create_validation_summary(
    errors: tuple[str, ...], warnings: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Create a validation summary dictionary.

    Args:
        errors: Tuple of error messages.
        warnings: Tuple of warning messages.

    Returns:
        Dictionary with validation status information.
    """
    if len(errors) > 0:
        status = "failure"
        is_valid = False
    elif len(warnings) > 0:
        status = "partial"
        is_valid = True
    else:
        status = "success"
        is_valid = True

    return {
        "status": status,
        "is_valid": is_valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
