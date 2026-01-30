from typing import Any

from pydantic import BaseModel, ConfigDict

from strict.integrity.schemas import (
    ProcessingRequest,
    SignalConfig,
    SignalType,
    ProcessorType,
)


class HealthResponse(BaseModel):
    """Response model for health check."""

    model_config = ConfigDict(strict=True, frozen=True)
    status: str = "ok"
    version: str = "0.1.0"


class ValidationResponse(BaseModel):
    """Response model for validation endpoints."""

    model_config = ConfigDict(strict=True, frozen=True)
    valid: bool
    errors: list[str]
    validated_data: dict[str, Any] | None = None


class SignalConfigDTO(BaseModel):
    """Data Transfer Object for SignalConfig.

    Accepts loose input (strings for enums, etc.) and parses it into
    the strict SignalConfig domain model.
    """

    signal_type: str | SignalType
    sampling_rate: float
    frequency: float
    amplitude: float
    duration: float
    channels: int = 1

    def to_domain(self) -> SignalConfig:
        """Convert to strict domain model."""
        # Explicitly convert string to Enum if needed
        sig_type = self.signal_type
        if isinstance(sig_type, str):
            sig_type = SignalType(sig_type)

        return SignalConfig(
            signal_type=sig_type,
            sampling_rate=self.sampling_rate,
            frequency=self.frequency,
            amplitude=self.amplitude,
            duration=self.duration,
            channels=self.channels,
        )


class ProcessingRequestDTO(BaseModel):
    """Data Transfer Object for ProcessingRequest."""

    input_data: str
    input_tokens: int
    processor_type: str | ProcessorType = "hybrid"
    token_threshold: int = 500
    max_retries: int = 3
    timeout_seconds: float = 30.0

    def to_domain(self) -> ProcessingRequest:
        """Convert to strict domain model."""
        proc_type = self.processor_type
        if isinstance(proc_type, str):
            proc_type = ProcessorType(proc_type)

        return ProcessingRequest(
            input_data=self.input_data,
            input_tokens=self.input_tokens,
            processor_type=proc_type,
            token_threshold=self.token_threshold,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
        )
