"""Tests for the Core Math Engine.

This module verifies the mathematical formulas and pure functions
in the Core layer.

Test Strategy:
- Formula correctness verification
- Edge case handling
- Pure function behavior validation
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ConfigDict

from strict.core.math_engine import (
    calculate_availability,
    calculate_combined_availability,
    calculate_nyquist_frequency,
    calculate_required_sampling_rate,
    calculate_sample_count,
    calculate_system_success_from_config,
    calculate_system_success_probability,
    determine_processor,
    validate_model_output,
    validate_with_retry,
)
from strict.integrity.schemas import FailoverConfig


class TestValidateModelOutput:
    """Tests for the validation function: Output = f_validate(Model(x), Schema)."""

    def test_valid_input_returns_model(self) -> None:
        """Valid input should return validated model with no errors."""

        class SimpleModel(BaseModel):
            model_config = ConfigDict(strict=True)
            name: str
            value: int

        result, errors = validate_model_output(
            {"name": "test", "value": 42},
            SimpleModel,
        )
        assert result is not None
        assert result.name == "test"
        assert result.value == 42
        assert errors == []

    def test_invalid_input_returns_errors(self) -> None:
        """Invalid input should return None with error messages."""

        class SimpleModel(BaseModel):
            model_config = ConfigDict(strict=True)
            name: str
            value: int

        result, errors = validate_model_output(
            {"name": "test", "value": "not_an_int"},
            SimpleModel,
        )
        assert result is None
        assert len(errors) > 0
        assert any("value" in e for e in errors)

    def test_missing_field_returns_errors(self) -> None:
        """Missing required field should return errors."""

        class SimpleModel(BaseModel):
            model_config = ConfigDict(strict=True)
            name: str
            value: int

        result, errors = validate_model_output(
            {"name": "test"},  # Missing 'value'
            SimpleModel,
        )
        assert result is None
        assert len(errors) > 0

    def test_idempotence(self) -> None:
        """Validating the same input should always produce the same result."""

        class SimpleModel(BaseModel):
            model_config = ConfigDict(strict=True)
            x: int

        input_data = {"x": 10}

        result1, errors1 = validate_model_output(input_data, SimpleModel)
        result2, errors2 = validate_model_output(input_data, SimpleModel)

        assert result1 is not None
        assert result2 is not None
        assert result1.x == result2.x
        assert errors1 == errors2


class TestValidateWithRetry:
    """Tests for validation with retry logic."""

    def test_valid_input_no_retries(self) -> None:
        """Valid input should succeed on first attempt."""

        class SimpleModel(BaseModel):
            value: int

        result, errors, retries = validate_with_retry(
            {"value": 42},
            SimpleModel,
        )
        assert result is not None
        assert result.value == 42
        assert retries == 0

    def test_invalid_input_exhausts_retries(self) -> None:
        """Invalid input should exhaust all retries."""

        class SimpleModel(BaseModel):
            model_config = ConfigDict(strict=True)
            value: int

        result, errors, retries = validate_with_retry(
            {"value": "not_int"},
            SimpleModel,
            max_retries=3,
        )
        assert result is None
        assert len(errors) > 0
        assert retries == 3

    def test_transform_function_applied(self) -> None:
        """Transform function should be applied between retries."""

        class SimpleModel(BaseModel):
            value: int

        call_count = 0

        def fix_value(data: dict, errors: list) -> dict:
            nonlocal call_count
            call_count += 1
            return {"value": 42}

        result, errors, retries = validate_with_retry(
            {"value": "invalid"},
            SimpleModel,
            max_retries=3,
            transform_fn=fix_value,
        )
        # Should succeed after transform
        assert result is not None or call_count > 0


class TestSystemSuccessProbability:
    """Tests for: P(System Success) = 1 - (P(Cloud Fail) * P(Local Fail))."""

    def test_formula_with_failover(self) -> None:
        """Verify formula with failover enabled."""
        # P(Success) = 1 - (0.01 * 0.05) = 0.9995
        p_success = calculate_system_success_probability(0.01, 0.05, True)
        assert abs(p_success - 0.9995) < 1e-10

    def test_formula_without_failover(self) -> None:
        """Without failover, only cloud matters."""
        # P(Success) = 1 - 0.01 = 0.99
        p_success = calculate_system_success_probability(0.01, 0.05, False)
        assert abs(p_success - 0.99) < 1e-10

    def test_zero_failure_probabilities(self) -> None:
        """Zero failure probability means 100% success."""
        p_success = calculate_system_success_probability(0.0, 0.0, True)
        assert p_success == 1.0

    def test_one_failure_probability(self) -> None:
        """If one system always fails, failover should still work."""
        # Cloud always fails, but local has 5% failure
        p_success = calculate_system_success_probability(1.0, 0.05, True)
        # P(Success) = 1 - (1.0 * 0.05) = 0.95
        assert abs(p_success - 0.95) < 1e-10

    def test_both_always_fail(self) -> None:
        """If both always fail, system always fails."""
        p_success = calculate_system_success_probability(1.0, 1.0, True)
        assert p_success == 0.0

    def test_from_config(self) -> None:
        """Test calculation from FailoverConfig model."""
        config = FailoverConfig(
            cloud_failure_probability=0.02,
            local_failure_probability=0.03,
            enable_failover=True,
        )
        p_success = calculate_system_success_from_config(config)
        expected = 1.0 - (0.02 * 0.03)
        assert abs(p_success - expected) < 1e-10


class TestProcessorRouting:
    """Tests for processor routing logic."""

    def test_below_threshold_uses_local(self) -> None:
        """Tokens below threshold should use local processor."""
        processor = determine_processor(400, token_threshold=500)
        assert processor == "local"

    def test_above_threshold_uses_cloud(self) -> None:
        """Tokens above threshold should use cloud processor."""
        processor = determine_processor(600, token_threshold=500)
        assert processor == "cloud"

    def test_at_threshold_uses_local(self) -> None:
        """Tokens at exactly threshold should use local."""
        processor = determine_processor(500, token_threshold=500)
        assert processor == "local"

    def test_custom_threshold(self) -> None:
        """Custom threshold should be respected."""
        processor = determine_processor(150, token_threshold=100)
        assert processor == "cloud"


class TestSignalProcessing:
    """Tests for signal processing functions."""

    def test_nyquist_frequency(self) -> None:
        """Nyquist frequency is half the sampling rate."""
        assert calculate_nyquist_frequency(44100.0) == 22050.0
        assert calculate_nyquist_frequency(48000.0) == 24000.0

    def test_required_sampling_rate(self) -> None:
        """Required sampling rate should exceed Nyquist with margin."""
        # For 1000 Hz signal, Nyquist rate is 2000 Hz
        # With 10% margin, required is 2200 Hz
        required = calculate_required_sampling_rate(1000.0, margin=1.1)
        assert abs(required - 2200.0) < 1e-10

    def test_sample_count(self) -> None:
        """Sample count should be duration * rate."""
        count = calculate_sample_count(1.0, 44100.0)
        assert count == 44100

        count = calculate_sample_count(0.1, 44100.0)
        assert count == 4410


class TestAvailabilityCalculations:
    """Tests for reliability/availability functions."""

    def test_availability_formula(self) -> None:
        """Test A = MTBF / (MTBF + MTTR)."""
        # 99% uptime: MTBF=99, MTTR=1
        availability = calculate_availability(99.0, 1.0)
        assert abs(availability - 0.99) < 1e-10

    def test_combined_availability_parallel(self) -> None:
        """Parallel systems have higher combined availability."""
        # Two 90% available systems in parallel
        # A = 1 - (0.1 * 0.1) = 0.99
        combined = calculate_combined_availability([0.9, 0.9], parallel=True)
        assert abs(combined - 0.99) < 1e-10

    def test_combined_availability_series(self) -> None:
        """Series systems have lower combined availability."""
        # Two 90% available systems in series
        # A = 0.9 * 0.9 = 0.81
        combined = calculate_combined_availability([0.9, 0.9], parallel=False)
        assert abs(combined - 0.81) < 1e-10

    def test_empty_availability_list(self) -> None:
        """Empty list should return 0."""
        assert calculate_combined_availability([]) == 0.0

    def test_single_component(self) -> None:
        """Single component has same availability in both modes."""
        assert calculate_combined_availability([0.95], parallel=True) == 0.95
        assert calculate_combined_availability([0.95], parallel=False) == 0.95


class TestPureFunctionBehavior:
    """Tests to verify pure function behavior."""

    def test_no_side_effects(self) -> None:
        """Functions should not modify their inputs."""
        input_data = {"name": "test", "value": 42}
        original = input_data.copy()

        class SimpleModel(BaseModel):
            name: str
            value: int

        validate_model_output(input_data, SimpleModel)
        assert input_data == original

    def test_deterministic_results(self) -> None:
        """Same input should always produce same output."""
        results = [
            calculate_system_success_probability(0.01, 0.05)
            for _ in range(100)
        ]
        assert all(r == results[0] for r in results)

    def test_referential_transparency(self) -> None:
        """Function can be replaced with its return value."""
        # Calculate once
        result = calculate_system_success_probability(0.01, 0.05)

        # The value 0.9995 could replace any call with same args
        expected = 1.0 - (0.01 * 0.05)
        assert result == expected
