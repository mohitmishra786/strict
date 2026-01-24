"""Tests for the Integrity Layer (The Gatekeeper).

This module contains fuzz testing and edge case validation for
the Pydantic models in the Integrity Layer.

Test Strategy:
- Valid input acceptance
- Invalid input rejection
- Edge case handling
- Cross-field validation
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from rough.integrity.schemas import (
    FailoverConfig,
    OutputSchema,
    ProcessingRequest,
    ProcessorType,
    SignalConfig,
    SignalType,
    ValidationResult,
    ValidationStatus,
)
from rough.integrity.validators import (
    collect_validation_errors,
    compute_input_hash,
    create_validation_summary,
    is_valid_amplitude,
    is_valid_frequency,
    is_valid_probability,
    validate_nyquist_criterion,
    validate_token_processor_compatibility,
)


class TestSignalConfig:
    """Tests for SignalConfig model."""

    def test_valid_analog_signal(self) -> None:
        """Valid analog signal should be accepted."""
        config = SignalConfig(
            signal_type=SignalType.ANALOG,
            sampling_rate=44100.0,
            frequency=440.0,
            amplitude=0.5,
            duration=1.0,
        )
        assert config.signal_type == SignalType.ANALOG
        assert config.sampling_rate == 44100.0
        assert config.frequency == 440.0

    def test_valid_digital_signal(self) -> None:
        """Valid digital signal should be accepted."""
        config = SignalConfig(
            signal_type=SignalType.DIGITAL,
            sampling_rate=48000.0,
            frequency=1000.0,
            amplitude=0.8,
            duration=2.5,
            channels=2,
        )
        assert config.signal_type == SignalType.DIGITAL
        assert config.channels == 2

    def test_negative_frequency_rejected(self) -> None:
        """Negative frequency should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SignalConfig(
                signal_type=SignalType.ANALOG,
                sampling_rate=44100.0,
                frequency=-100.0,
                amplitude=0.5,
                duration=1.0,
            )
        assert "frequency" in str(exc_info.value).lower()

    def test_zero_sampling_rate_rejected(self) -> None:
        """Zero sampling rate should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SignalConfig(
                signal_type=SignalType.ANALOG,
                sampling_rate=0.0,
                frequency=440.0,
                amplitude=0.5,
                duration=1.0,
            )
        assert "sampling_rate" in str(exc_info.value).lower()

    def test_amplitude_at_boundary_rejected(self) -> None:
        """Amplitude of exactly 1.0 should be rejected (must be < 1.0)."""
        with pytest.raises(ValidationError) as exc_info:
            SignalConfig(
                signal_type=SignalType.ANALOG,
                sampling_rate=44100.0,
                frequency=440.0,
                amplitude=1.0,
                duration=1.0,
            )
        assert "amplitude" in str(exc_info.value).lower()

    def test_nyquist_criterion_violated(self) -> None:
        """Analog signal violating Nyquist criterion should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SignalConfig(
                signal_type=SignalType.ANALOG,
                sampling_rate=1000.0,
                frequency=600.0,  # Nyquist rate = 1200, but sampling is only 1000
                amplitude=0.5,
                duration=1.0,
            )
        assert "nyquist" in str(exc_info.value).lower()

    def test_nyquist_criterion_satisfied(self) -> None:
        """Analog signal satisfying Nyquist criterion should be accepted."""
        config = SignalConfig(
            signal_type=SignalType.ANALOG,
            sampling_rate=3000.0,
            frequency=1000.0,  # Nyquist rate = 2000, sampling is 3000
            amplitude=0.5,
            duration=1.0,
        )
        assert config.sampling_rate > 2 * config.frequency

    def test_digital_signal_no_nyquist_check(self) -> None:
        """Digital signals should not be subject to Nyquist check."""
        # This would fail Nyquist for analog, but should pass for digital
        config = SignalConfig(
            signal_type=SignalType.DIGITAL,
            sampling_rate=1000.0,
            frequency=600.0,
            amplitude=0.5,
            duration=1.0,
        )
        assert config.signal_type == SignalType.DIGITAL

    def test_immutability(self) -> None:
        """Config should be immutable (frozen)."""
        config = SignalConfig(
            signal_type=SignalType.ANALOG,
            sampling_rate=44100.0,
            frequency=440.0,
            amplitude=0.5,
            duration=1.0,
        )
        with pytest.raises(ValidationError):
            config.frequency = 880.0  # type: ignore

    def test_strict_mode_rejects_string_numbers(self) -> None:
        """Strict mode should reject string representations of numbers."""
        with pytest.raises(ValidationError):
            SignalConfig(
                signal_type=SignalType.ANALOG,
                sampling_rate="44100.0",  # type: ignore
                frequency=440.0,
                amplitude=0.5,
                duration=1.0,
            )


class TestProcessingRequest:
    """Tests for ProcessingRequest model."""

    def test_valid_request(self) -> None:
        """Valid processing request should be accepted."""
        request = ProcessingRequest(
            input_data="Hello, world!",
            input_tokens=3,
            processor_type=ProcessorType.HYBRID,
        )
        assert request.input_tokens == 3
        assert request.processor_type == ProcessorType.HYBRID

    def test_empty_input_rejected(self) -> None:
        """Empty input data should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingRequest(
                input_data="",
                input_tokens=0,
            )
        assert "input_data" in str(exc_info.value).lower()

    def test_local_processor_token_limit(self) -> None:
        """Local processor should reject inputs exceeding token limit."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingRequest(
                input_data="x" * 100,
                input_tokens=5000,  # Exceeds local limit of 4096
                processor_type=ProcessorType.LOCAL,
            )
        assert "local" in str(exc_info.value).lower()

    def test_cloud_processor_handles_large_tokens(self) -> None:
        """Cloud processor should accept large token counts."""
        request = ProcessingRequest(
            input_data="x" * 100,
            input_tokens=100000,
            processor_type=ProcessorType.CLOUD,
        )
        assert request.input_tokens == 100000


class TestFailoverConfig:
    """Tests for FailoverConfig model."""

    def test_valid_config(self) -> None:
        """Valid failover config should be accepted."""
        config = FailoverConfig(
            cloud_failure_probability=0.01,
            local_failure_probability=0.05,
            enable_failover=True,
        )
        assert config.cloud_failure_probability == 0.01

    def test_probability_out_of_range_rejected(self) -> None:
        """Probability > 1.0 should be rejected."""
        with pytest.raises(ValidationError):
            FailoverConfig(
                cloud_failure_probability=1.5,
                local_failure_probability=0.05,
            )

    def test_system_success_with_failover(self) -> None:
        """Test system success probability calculation with failover."""
        config = FailoverConfig(
            cloud_failure_probability=0.01,
            local_failure_probability=0.05,
            enable_failover=True,
        )
        expected = 1.0 - (0.01 * 0.05)  # 0.9995
        assert abs(config.system_success_probability - expected) < 1e-10

    def test_system_success_without_failover(self) -> None:
        """Test system success probability without failover."""
        config = FailoverConfig(
            cloud_failure_probability=0.01,
            local_failure_probability=0.05,
            enable_failover=False,
        )
        expected = 1.0 - 0.01  # 0.99
        assert abs(config.system_success_probability - expected) < 1e-10


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_success_result(self) -> None:
        """Valid success result should be accepted."""
        result = ValidationResult(
            status=ValidationStatus.SUCCESS,
            is_valid=True,
            input_hash="abc123",
        )
        assert result.is_valid is True
        assert result.errors == ()

    def test_inconsistent_status_rejected(self) -> None:
        """Inconsistent status and is_valid should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                status=ValidationStatus.SUCCESS,
                is_valid=False,  # Inconsistent with SUCCESS
                input_hash="abc123",
            )
        assert "success" in str(exc_info.value).lower()

    def test_success_with_errors_rejected(self) -> None:
        """SUCCESS status with errors should be rejected."""
        with pytest.raises(ValidationError):
            ValidationResult(
                status=ValidationStatus.SUCCESS,
                is_valid=True,
                input_hash="abc123",
                errors=("Some error",),
            )


class TestValidators:
    """Tests for validator functions."""

    def test_compute_input_hash(self) -> None:
        """Hash computation should be deterministic."""
        hash1 = compute_input_hash("test input")
        hash2 = compute_input_hash("test input")
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_is_valid_frequency(self) -> None:
        """Test frequency validation."""
        assert is_valid_frequency(440.0) is True
        assert is_valid_frequency(0.0) is False
        assert is_valid_frequency(-100.0) is False
        assert is_valid_frequency(float("inf")) is False

    def test_is_valid_probability(self) -> None:
        """Test probability validation."""
        assert is_valid_probability(0.5) is True
        assert is_valid_probability(0.0) is True
        assert is_valid_probability(1.0) is True
        assert is_valid_probability(-0.1) is False
        assert is_valid_probability(1.1) is False

    def test_is_valid_amplitude(self) -> None:
        """Test amplitude validation."""
        assert is_valid_amplitude(0.5) is True
        assert is_valid_amplitude(0.0) is True
        assert is_valid_amplitude(0.99) is True
        assert is_valid_amplitude(1.0) is False  # Must be < 1.0
        assert is_valid_amplitude(-0.1) is False

    def test_validate_nyquist_criterion(self) -> None:
        """Test Nyquist criterion validation."""
        is_valid, error = validate_nyquist_criterion(44100.0, 440.0)
        assert is_valid is True
        assert error == ""

        is_valid, error = validate_nyquist_criterion(1000.0, 600.0)
        assert is_valid is False
        assert "nyquist" in error.lower()

    def test_validate_token_processor_compatibility(self) -> None:
        """Test token-processor compatibility."""
        is_valid, _ = validate_token_processor_compatibility(100, "local")
        assert is_valid is True

        is_valid, error = validate_token_processor_compatibility(5000, "local")
        assert is_valid is False
        assert "5000" in error

    def test_collect_validation_errors(self) -> None:
        """Test error collection."""
        validations = [
            (True, ""),
            (False, "Error 1"),
            (True, ""),
            (False, "Error 2"),
        ]
        errors = collect_validation_errors(validations)
        assert errors == ("Error 1", "Error 2")

    def test_create_validation_summary(self) -> None:
        """Test validation summary creation."""
        summary = create_validation_summary(())
        assert summary["status"] == "success"
        assert summary["is_valid"] is True

        summary = create_validation_summary(("Error",))
        assert summary["status"] == "failure"
        assert summary["is_valid"] is False

        summary = create_validation_summary((), ("Warning",))
        assert summary["status"] == "partial"
        assert summary["is_valid"] is True
