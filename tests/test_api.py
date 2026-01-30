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


def get_auth_headers():
    """Helper to get auth headers."""
    response = client.post("/token", data={"username": "admin", "password": "secret"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_metrics_endpoint():
    """Test that Prometheus metrics endpoint is exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_validate_signal_valid():
    """Test validating a valid signal config."""
    valid_data = {
        "signal_type": "analog",
        "sampling_rate": 44100.0,
        "frequency": 440.0,
        "amplitude": 0.5,
        "duration": 1.0,
    }
    response = client.post(
        "/validate/signal", json=valid_data, headers=get_auth_headers()
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validate_signal_unauthorized():
    """Test validating without auth."""
    valid_data = {
        "signal_type": "analog",
        "sampling_rate": 44100.0,
        "frequency": 440.0,
        "amplitude": 0.5,
        "duration": 1.0,
    }
    response = client.post("/validate/signal", json=valid_data)
    assert response.status_code == 401


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
    response = client.post(
        "/process/request", json=request_data, headers=get_auth_headers()
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "Mocked result"
