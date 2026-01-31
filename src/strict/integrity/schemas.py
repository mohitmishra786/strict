"""Strict Pydantic V2 Models - The Gatekeeper.

This module defines the immutable, strictly-typed models that form the
Integrity Layer of the Diamond Gate Protocol. All inputs must be parsed
into these models before reaching the Core.

Design Principles:
- ConfigDict(strict=True, frozen=True) for immutability
- Annotated types with Field() constraints for physical limits
- @model_validator(mode='after') for cross-field consistency
- Never use bare float or int - always constrain with Annotated
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# -----------------------------------------------------------------------------
# Type Aliases with Physical Constraints
# -----------------------------------------------------------------------------

# Positive float that cannot be zero, infinity, or NaN
PositiveFloat = Annotated[
    float,
    Field(gt=0, allow_inf_nan=False, description="Positive float, no infinity or NaN"),
]

# Non-negative float (zero allowed)
NonNegativeFloat = Annotated[
    float,
    Field(ge=0, allow_inf_nan=False, description="Non-negative float"),
]

# Probability value between 0 and 1 inclusive
Probability = Annotated[
    float,
    Field(ge=0, le=1, allow_inf_nan=False, description="Probability value [0, 1]"),
]

# Amplitude value between 0 and 1 (normalized)
Amplitude = Annotated[
    float,
    Field(ge=0, lt=1, allow_inf_nan=False, description="Normalized amplitude [0, 1)"),
]

# Positive integer
PositiveInt = Annotated[
    int,
    Field(gt=0, description="Positive integer"),
]

# Non-negative integer
NonNegativeInt = Annotated[
    int,
    Field(ge=0, description="Non-negative integer"),
]

# Token count (positive integer)
TokenCount = Annotated[
    int,
    Field(gt=0, le=1_000_000, description="Token count, max 1M"),
]


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class SignalType(str, Enum):
    """Type of signal being processed."""

    ANALOG = "analog"
    DIGITAL = "digital"
    HYBRID = "hybrid"


class ProcessorType(str, Enum):
    """Type of processor to use for computation."""

    CLOUD = "cloud"  # e.g., GPT-4, Claude
    LOCAL = "local"  # e.g., local Llama-3
    HYBRID = "hybrid"  # Fallback strategy


class ValidationStatus(str, Enum):
    """Status of validation result."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class Region(str, Enum):
    """Supported deployment regions."""

    US_EAST = "us-east-1"
    US_WEST = "us-west-2"
    EU_CENTRAL = "eu-central-1"
    AP_SOUTHEAST = "ap-southeast-1"


class RegionConfig(BaseModel):
    """Configuration for a specific region."""

    model_config = ConfigDict(strict=True, frozen=True)

    region: Region
    endpoint: str
    latency_ms: float = Field(default=0.0, ge=0.0)
    is_active: bool = True


class GeoRoutingConfig(BaseModel):
    """Configuration for multi-region geo-routing."""

    model_config = ConfigDict(strict=True, frozen=True)

    regions: tuple[RegionConfig, ...]
    primary_region: Region
    failover_enabled: bool = True


class FeatureType(str, Enum):
    """Type of feature in an ML model."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TEXT = "text"


# -----------------------------------------------------------------------------
# Immutable Models
# -----------------------------------------------------------------------------


class FeatureSchema(BaseModel):
    """Schema for an ML model feature."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(min_length=1, max_length=100)
    feature_type: FeatureType
    description: str | None = None
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: tuple[Any, ...] | None = None


class MLModelConfig(BaseModel):
    """Configuration for an ML model."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(min_length=1, max_length=100)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    features: tuple[FeatureSchema, ...]
    performance_threshold: Probability = Field(default=0.8)
    current_performance: Probability | None = None
    last_evaluated: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MLModelValidationRequest(BaseModel):
    """Request for ML model input validation."""

    model_config = ConfigDict(strict=True, frozen=True)

    model_info: MLModelConfig
    input_features: dict[str, Any]

    def validate_inputs(self) -> ValidationResult:
        """Validate input features against the model schema.

        Returns:
            ValidationResult with any errors found.
        """
        from strict.integrity.validators import (
            validate_feature_value,
            compute_input_hash,
        )
        import json

        errors = []
        # Check if all required features are present
        schema_features = {f.name: f for f in self.model_info.features}

        # Check for missing required features
        for name, schema in schema_features.items():
            if schema.required and name not in self.input_features:
                errors.append(f"Missing required feature: {name}")

        # Validate provided features
        for name, value in self.input_features.items():
            if name not in schema_features:
                # Optional: Handle extra features? For strictness, we might reject them.
                # errors.append(f"Unknown feature: {name}")
                continue

            is_valid, error_msg = validate_feature_value(value, schema_features[name])
            if not is_valid:
                errors.append(error_msg)

        input_hash = compute_input_hash(
            json.dumps(self.input_features, sort_keys=True)
        )[:16]

        if errors:
            return ValidationResult(
                status=ValidationStatus.FAILURE,
                is_valid=False,
                input_hash=input_hash,
                errors=tuple(errors),
            )

        return ValidationResult(
            status=ValidationStatus.SUCCESS,
            is_valid=True,
            input_hash=input_hash,
        )


class SignalData(BaseModel):
    """Raw signal data with basic validation.

    Used for signal processing operations.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    values: list[float] = Field(description="Signal sample values")
    sample_rate: PositiveFloat = Field(description="Sample rate in Hz")

    @model_validator(mode="after")
    def validate_signal_length(self) -> SignalData:
        """Ensure signal has at least one sample."""
        if len(self.values) == 0:
            raise ValueError("Signal data must contain at least one sample")
        return self

    def validate_integrity(self) -> ValidationResult:
        """Validate the signal data.

        Returns:
            ValidationResult with validation status.
        """
        import hashlib

        # Include both values and sample_rate in hash to avoid collisions
        # Note: Empty check already enforced by validate_signal_length model validator
        # Note: sample_rate > 0 already enforced by PositiveFloat type
        hash_input = f"{self.values}:{self.sample_rate}"
        input_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return ValidationResult(
            status=ValidationStatus.SUCCESS,
            is_valid=True,
            input_hash=input_hash,
            errors=(),
        )


class SignalConfig(BaseModel):
    """Configuration for signal processing with physical constraints.

    All fields are validated at the type level to ensure physical
    impossibilities (e.g., negative frequencies) are rejected immediately.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    signal_type: SignalType
    sampling_rate: PositiveFloat = Field(
        description="Sampling rate in Hz, must be positive for analog signals"
    )
    frequency: PositiveFloat = Field(description="Signal frequency in Hz")
    amplitude: Amplitude = Field(description="Normalized amplitude [0, 1)")
    duration: PositiveFloat = Field(description="Signal duration in seconds")
    channels: PositiveInt = Field(default=1, description="Number of channels")

    @model_validator(mode="after")
    def validate_nyquist_criterion(self) -> SignalConfig:
        """Ensure sampling rate satisfies Nyquist criterion.

        For analog signals, sampling_rate must be > 2 * frequency to avoid aliasing.
        """
        if self.signal_type == SignalType.ANALOG:
            nyquist_rate = 2 * self.frequency
            if self.sampling_rate <= nyquist_rate:
                raise ValueError(
                    f"Nyquist criterion violated: sampling_rate ({self.sampling_rate}) "
                    f"must be > 2 * frequency ({nyquist_rate}) for analog signals"
                )
        return self


class ProcessingRequest(BaseModel):
    """Request for processing with multi-stage validation.

    Implements the validation function: Output = f_validate(Model(x), Schema)
    """

    model_config = ConfigDict(strict=True, frozen=True)

    input_data: str = Field(
        min_length=1, max_length=1_000_000, description="Input data to process"
    )
    input_tokens: TokenCount = Field(description="Number of tokens in input")
    processor_type: ProcessorType = Field(
        default=ProcessorType.HYBRID, description="Processor selection strategy"
    )
    token_threshold: TokenCount = Field(
        default=500, description="Threshold for processor routing"
    )
    max_retries: NonNegativeInt = Field(
        default=3, description="Maximum retry attempts on failure"
    )
    timeout_seconds: PositiveFloat = Field(
        default=30.0, description="Request timeout in seconds"
    )

    @model_validator(mode="after")
    def validate_processor_routing(self) -> ProcessingRequest:
        """Validate processor routing logic.

        If processor_type is CLOUD and input exceeds local capability,
        ensure we have appropriate settings.
        """
        if self.processor_type == ProcessorType.LOCAL and self.input_tokens > 4096:
            raise ValueError(
                f"Local processor cannot handle {self.input_tokens} tokens. "
                "Maximum is 4096. Use CLOUD or HYBRID processor_type."
            )
        return self


class FailoverConfig(BaseModel):
    """Configuration for failover logic between cloud and local processors.

    Implements: P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))
    """

    model_config = ConfigDict(strict=True, frozen=True)

    cloud_failure_probability: Probability = Field(
        default=0.01, description="Probability of cloud processor failure"
    )
    local_failure_probability: Probability = Field(
        default=0.05, description="Probability of local processor failure"
    )
    enable_failover: bool = Field(
        default=True, description="Enable automatic failover to local on cloud failure"
    )
    failover_timeout_ms: PositiveInt = Field(
        default=5000, description="Timeout before triggering failover (milliseconds)"
    )

    @property
    def system_success_probability(self) -> float:
        """Calculate system success probability.

        P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))

        With failover enabled, system only fails if BOTH cloud and local fail.
        Without failover, system fails if cloud fails.
        """
        if self.enable_failover:
            return 1.0 - (
                self.cloud_failure_probability * self.local_failure_probability
            )
        return 1.0 - self.cloud_failure_probability


class ValidationResult(BaseModel):
    """Result of model validation.

    Used to wrap outputs and provide structured error information.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    status: ValidationStatus
    is_valid: bool
    input_hash: str = Field(description="Hash of the input for traceability")
    errors: tuple[str, ...] = Field(default=(), description="Validation error messages")
    warnings: tuple[str, ...] = Field(
        default=(), description="Validation warning messages"
    )

    @model_validator(mode="after")
    def validate_status_consistency(self) -> ValidationResult:
        """Ensure status and is_valid are consistent."""
        if self.status == ValidationStatus.SUCCESS and not self.is_valid:
            raise ValueError("Status is SUCCESS but is_valid is False")
        if self.status == ValidationStatus.FAILURE and self.is_valid:
            raise ValueError("Status is FAILURE but is_valid is True")
        if self.status == ValidationStatus.SUCCESS and len(self.errors) > 0:
            raise ValueError("Status is SUCCESS but errors are present")
        return self


class OutputSchema(BaseModel):
    """Standardized output schema for Layer 4.

    All outputs from the Core are serialized into this schema.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    result: Any = Field(description="The computation result")
    validation: ValidationResult = Field(description="Validation metadata")
    processor_used: ProcessorType = Field(description="Which processor was used")
    processing_time_ms: NonNegativeFloat = Field(
        description="Processing time in milliseconds"
    )
    retries_attempted: NonNegativeInt = Field(
        default=0, description="Number of retries attempted"
    )
