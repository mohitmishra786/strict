import pytest
from pydantic import ValidationError
from strict.integrity.schemas import (
    MLModelConfig,
    FeatureSchema,
    FeatureType,
    MLModelValidationRequest,
    ValidationStatus,
)


class TestMLModelValidation:
    """Tests for ML Model Validation."""

    @pytest.fixture
    def model_config(self) -> MLModelConfig:
        return MLModelConfig(
            name="sentiment_classifier",
            version="1.0.0",
            features=(
                FeatureSchema(name="text", feature_type=FeatureType.TEXT),
                FeatureSchema(
                    name="confidence_threshold",
                    feature_type=FeatureType.NUMERIC,
                    min_value=0.0,
                    max_value=1.0,
                    required=False,
                ),
                FeatureSchema(
                    name="category",
                    feature_type=FeatureType.CATEGORICAL,
                    allowed_values=("news", "sports", "tech"),
                ),
            ),
        )

    def test_valid_ml_input(self, model_config: MLModelConfig) -> None:
        """Valid ML input should pass validation."""
        request = MLModelValidationRequest(
            model_info=model_config,
            input_features={
                "text": "The game was amazing!",
                "confidence_threshold": 0.9,
                "category": "sports",
            },
        )
        result = request.validate_inputs()
        assert result.status == ValidationStatus.SUCCESS
        assert result.is_valid is True
        assert not result.errors

    def test_missing_required_feature(self, model_config: MLModelConfig) -> None:
        """Missing required feature should fail validation."""
        request = MLModelValidationRequest(
            model_info=model_config,
            input_features={
                # "text" is missing
                "category": "tech",
            },
        )
        result = request.validate_inputs()
        assert result.status == ValidationStatus.FAILURE
        assert any("text" in err.lower() for err in result.errors)

    def test_invalid_numeric_range(self, model_config: MLModelConfig) -> None:
        """Numeric value out of range should fail validation."""
        request = MLModelValidationRequest(
            model_info=model_config,
            input_features={
                "text": "Valid text",
                "confidence_threshold": 1.5,  # Max is 1.0
                "category": "tech",
            },
        )
        result = request.validate_inputs()
        assert result.status == ValidationStatus.FAILURE
        assert any("1.5" in err for err in result.errors)

    def test_invalid_categorical_value(self, model_config: MLModelConfig) -> None:
        """Value not in allowed_values should fail validation."""
        request = MLModelValidationRequest(
            model_info=model_config,
            input_features={
                "text": "Valid text",
                "category": "fashion",  # Not allowed
            },
        )
        result = request.validate_inputs()
        assert result.status == ValidationStatus.FAILURE
        assert any("fashion" in err for err in result.errors)

    def test_unknown_feature(self, model_config: MLModelConfig) -> None:
        """Unknown feature should fail validation in strict mode."""
        request = MLModelValidationRequest(
            model_info=model_config,
            input_features={
                "text": "Valid text",
                "unknown_field": "some value",
            },
        )
        result = request.validate_inputs()
        assert result.status == ValidationStatus.FAILURE
        assert any("unknown feature" in err.lower() for err in result.errors)

    def test_model_version_pattern(self) -> None:
        """Model version must follow semver pattern."""
        with pytest.raises(ValidationError):
            MLModelConfig(
                name="test",
                version="v1",  # Invalid
                features=(),
            )

        MLModelConfig(
            name="test",
            version="1.2.3",  # Valid
            features=(),
        )
