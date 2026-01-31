"""Integrity module - The Gatekeeper.

This module contains the critical Pydantic V2 validation layer.
All inputs must pass through here before reaching the Core.
"""

from strict.integrity.schemas import (
    SignalConfig,
    ProcessingRequest,
    ValidationResult,
    OutputSchema,
)

__all__ = [
    "SignalConfig",
    "ProcessingRequest",
    "ValidationResult",
    "OutputSchema",
]
