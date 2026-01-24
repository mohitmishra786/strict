"""Pure Mathematical Functions - The Math Engine.

This module contains ONLY pure, stateless functions.
No I/O, no prints, no database calls - just math.

Design Principles:
- Same input always produces same output
- No side effects
- Trivially testable and parallelizable
- Accepts ONLY validated models from the Integrity Layer

Formulas Implemented:
1. Validation Function: Output = f_validate(Model(x), Schema)
2. System Success Probability: P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from rough.integrity.schemas import FailoverConfig, ProcessingRequest


# Type variable for generic model validation
T = TypeVar("T", bound=BaseModel)


# -----------------------------------------------------------------------------
# Formula 1: Validation Function
# Output = f_validate(Model(x), Schema)
# -----------------------------------------------------------------------------


def validate_model_output(
    raw_input: dict[str, Any],
    schema: type[T],
) -> tuple[T | None, list[str]]:
    """Validate raw input against a Pydantic schema.

    Implements: Output = f_validate(Model(x), Schema)

    This function parses raw input into a strictly-typed model.
    If parsing fails, the input is rejected with structured errors.

    Args:
        raw_input: Raw dictionary input from Layer 1 (Dirty Edge).
        schema: The Pydantic model class to validate against.

    Returns:
        Tuple of (validated_model, errors).
        If validation succeeds, errors is empty.
        If validation fails, validated_model is None.

    Example:
        >>> from rough.integrity.schemas import SignalConfig
        >>> result, errors = validate_model_output(
        ...     {"signal_type": "analog", "sampling_rate": 44100.0, ...},
        ...     SignalConfig
        ... )
        >>> if errors:
        ...     handle_validation_errors(errors)
        ... else:
        ...     process_signal(result)
    """
    try:
        validated = schema.model_validate(raw_input)
        return (validated, [])
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return (None, errors)


def validate_with_retry(
    raw_input: dict[str, Any],
    schema: type[T],
    max_retries: int = 3,
    transform_fn: callable | None = None,
) -> tuple[T | None, list[str], int]:
    """Validate with optional transformation and retry logic.

    If validation fails and a transform function is provided,
    apply the transformation and retry.

    Args:
        raw_input: Raw dictionary input.
        schema: The Pydantic model class to validate against.
        max_retries: Maximum number of retry attempts.
        transform_fn: Optional function to transform input between retries.

    Returns:
        Tuple of (validated_model, errors, retry_count).
    """
    errors: list[str] = []
    current_input = raw_input.copy()

    for attempt in range(max_retries + 1):
        result, validation_errors = validate_model_output(current_input, schema)
        if result is not None:
            return (result, [], attempt)

        errors = validation_errors

        if transform_fn is not None and attempt < max_retries:
            current_input = transform_fn(current_input, validation_errors)

    return (None, errors, max_retries)


# -----------------------------------------------------------------------------
# Formula 2: System Success Probability
# P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))
# -----------------------------------------------------------------------------
def calculate_system_success_probability(
    cloud_failure_probability: float,
    local_failure_probability: float,
    failover_enabled: bool = True,
) -> float:
    """Calculate the probability of system success with failover.

    Implements: P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))

    With failover enabled, the system fails only if BOTH cloud and local
    processors fail. This significantly improves overall reliability.

    Args:
        cloud_failure_probability: P(Cloud Fail), must be in [0, 1].
        local_failure_probability: P(Local Fail), must be in [0, 1].
        failover_enabled: Whether automatic failover is enabled.

    Returns:
        The probability of system success, in [0, 1].

    Example:
        >>> # With 1% cloud failure and 5% local failure
        >>> p_success = calculate_system_success_probability(0.01, 0.05)
        >>> print(f"System success probability: {p_success:.4f}")
        System success probability: 0.9995
    """
    if failover_enabled:
        # P(System Fail) = P(Cloud Fail) * P(Local Fail)
        # P(System Success) = 1 - P(System Fail)
        return 1.0 - (cloud_failure_probability * local_failure_probability)
    else:
        # Without failover, system fails if cloud fails
        return 1.0 - cloud_failure_probability


def calculate_system_success_from_config(config: FailoverConfig) -> float:
    """Calculate system success probability from a FailoverConfig model.

    This is a convenience wrapper that extracts values from the config model.

    Args:
        config: A validated FailoverConfig model.

    Returns:
        The probability of system success.
    """
    return calculate_system_success_probability(
        cloud_failure_probability=config.cloud_failure_probability,
        local_failure_probability=config.local_failure_probability,
        failover_enabled=config.enable_failover,
    )


# -----------------------------------------------------------------------------
# Processor Routing Logic
# -----------------------------------------------------------------------------


def determine_processor(
    input_tokens: int,
    token_threshold: int = 500,
) -> str:
    """Determine which processor to use based on token count.

    Implements the routing rule:
    "If input length > 500 tokens, use GPT-4; else use spaCy."

    Args:
        input_tokens: Number of tokens in the input.
        token_threshold: Threshold for switching to cloud processor.

    Returns:
        "cloud" if tokens exceed threshold, "local" otherwise.
    """
    if input_tokens > token_threshold:
        return "cloud"
    return "local"


def route_request(request: ProcessingRequest) -> str:
    """Route a processing request to the appropriate processor.

    Uses the request's token count and threshold to determine routing.

    Args:
        request: A validated ProcessingRequest model.

    Returns:
        The processor type to use ("cloud" or "local").
    """
    if request.processor_type.value == "cloud":
        return "cloud"
    if request.processor_type.value == "local":
        return "local"

    # For hybrid, use the routing logic
    return determine_processor(
        input_tokens=request.input_tokens,
        token_threshold=request.token_threshold,
    )


# -----------------------------------------------------------------------------
# Signal Processing Functions
# -----------------------------------------------------------------------------


def calculate_nyquist_frequency(sampling_rate: float) -> float:
    """Calculate the Nyquist frequency for a given sampling rate.

    The Nyquist frequency is half the sampling rate and represents
    the maximum frequency that can be accurately represented.

    Args:
        sampling_rate: The sampling rate in Hz.

    Returns:
        The Nyquist frequency in Hz.
    """
    return sampling_rate / 2.0


def calculate_required_sampling_rate(max_frequency: float, margin: float = 1.1) -> float:
    """Calculate the minimum required sampling rate for a signal.

    Applies the Nyquist criterion with an optional safety margin.

    Args:
        max_frequency: The maximum frequency in the signal (Hz).
        margin: Safety margin multiplier (default 10% above Nyquist).

    Returns:
        The minimum required sampling rate in Hz.
    """
    nyquist_rate = 2.0 * max_frequency
    return nyquist_rate * margin


def calculate_sample_count(duration: float, sampling_rate: float) -> int:
    """Calculate the number of samples for a signal of given duration.

    Args:
        duration: Signal duration in seconds.
        sampling_rate: Sampling rate in Hz.

    Returns:
        The number of samples (rounded to nearest integer).
    """
    return int(round(duration * sampling_rate))


# -----------------------------------------------------------------------------
# Reliability Calculations
# -----------------------------------------------------------------------------


def calculate_availability(
    mtbf: float,
    mttr: float,
) -> float:
    """Calculate system availability from MTBF and MTTR.

    Availability = MTBF / (MTBF + MTTR)

    Args:
        mtbf: Mean Time Between Failures (in any time unit).
        mttr: Mean Time To Repair (in same time unit).

    Returns:
        Availability as a probability [0, 1].
    """
    return mtbf / (mtbf + mttr)


def calculate_combined_availability(
    availabilities: list[float],
    parallel: bool = True,
) -> float:
    """Calculate combined availability for multiple components.

    For parallel (redundant) systems:
        A_combined = 1 - product(1 - A_i)

    For series (sequential) systems:
        A_combined = product(A_i)

    Args:
        availabilities: List of individual component availabilities.
        parallel: If True, components are in parallel (redundant).
                 If False, components are in series.

    Returns:
        Combined system availability.
    """
    if not availabilities:
        return 0.0

    if parallel:
        # Parallel: system fails only if ALL components fail
        failure_prob = 1.0
        for a in availabilities:
            failure_prob *= (1.0 - a)
        return 1.0 - failure_prob
    else:
        # Series: system fails if ANY component fails
        combined = 1.0
        for a in availabilities:
            combined *= a
        return combined
