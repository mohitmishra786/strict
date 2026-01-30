from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from strict.api.server import app
from strict.integrity.schemas import (
    OutputSchema,
    ValidationResult,
    ValidationStatus,
    ProcessorType,
)

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_metrics_endpoint():
    """Test that Prometheus metrics endpoint is exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "strict_api_requests_total" in response.text or "# HELP" in response.text


def test_validate_signal_valid():
    """Test validating a valid signal config."""
    valid_data = {
        "signal_type": "analog",
        "sampling_rate": 44100.0,
        "frequency": 440.0,
        "amplitude": 0.5,
        "duration": 1.0,
    }
    response = client.post("/validate/signal", json=valid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["validated_data"]["frequency"] == 440.0


def test_validate_signal_invalid():
    """Test validating an invalid signal config (Nyquist violation)."""
    invalid_data = {
        "signal_type": "analog",
        "sampling_rate": 1000.0,
        "frequency": 600.0,  # Violation: 600 * 2 > 1000
        "amplitude": 0.5,
        "duration": 1.0,
    }
    response = client.post("/validate/signal", json=invalid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    # The error message comes from ValueError, so it might be in errors list
    # The implementation puts str(e) into errors list for ValueError
    assert any("Nyquist" in err for err in data["errors"])


@patch("strict.api.routes.processor_manager")
def test_process_request(mock_manager):
    """Test the processing request endpoint."""
    # Mock the processor manager
    mock_output = OutputSchema(
        result="Mocked result",
        validation=ValidationResult(
            status=ValidationStatus.SUCCESS,
            is_valid=True,
            input_hash="test",
            errors=(),
            warnings=(),
        ),
        processor_used=ProcessorType.LOCAL,
        processing_time_ms=10.0,
        retries_attempted=0,
    )
    mock_manager.process_request = AsyncMock(return_value=mock_output)

    request_data = {
        "input_data": "test input",
        "input_tokens": 100,
        "processor_type": "hybrid",
    }
    response = client.post("/process/request", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "Mocked result"
    assert data["processor_used"] == "local"
