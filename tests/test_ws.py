import pytest
from fastapi.testclient import TestClient
from strict.api.server import app


def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws/stream") as websocket:
        # Send a valid processing request
        websocket.send_json(
            {
                "input_data": "Test streaming",
                "input_tokens": 10,
                "processor_type": "local",
            }
        )

        # We expect at least one chunk and a 'done' message
        # Note: In test environment, OllamaProcessor might fail or return mock
        # depending on how it's implemented.
        try:
            response = websocket.receive_json()
            assert response["type"] in ["chunk", "error"]

            if response["type"] == "chunk":
                done = websocket.receive_json()
                assert done["type"] == "done"
        except Exception as e:
            # If Ollama is not running, we might get an error, which is acceptable for connection test
            pytest.fail(f"WebSocket communication failed: {e}")


def test_websocket_invalid_data():
    client = TestClient(app)
    with client.websocket_connect("/ws/stream") as websocket:
        # Send invalid data (missing required fields)
        websocket.send_json({"invalid": "data"})

        response = websocket.receive_json()
        assert response["type"] == "error"
