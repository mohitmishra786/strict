from fastapi.testclient import TestClient
from strict.api.server import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


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
    assert "Nyquist" in data["errors"][0]


def test_process_request():
    """Test the processing request endpoint."""
    request_data = {
        "input_data": "test input",
        "input_tokens": 100,
        "processor_type": "hybrid",
    }
    response = client.post("/process/request", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["processor_used"] == "local"  # 100 tokens < 500 threshold
