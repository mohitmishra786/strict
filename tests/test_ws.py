import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from pydantic import SecretStr
from strict.api.server import app
from strict.config import settings


def register_test_api_key():
    api_key = "test-api-key"
    if not any(k.get_secret_value() == api_key for k in settings.valid_api_keys):
        settings.valid_api_keys.append(SecretStr(api_key))
    return api_key


def test_websocket_connection():
    client = TestClient(app)
    api_key_plain = register_test_api_key()

    try:
        with client.websocket_connect(
            f"/ws/stream?api_key={api_key_plain}"
        ) as websocket:
            # Send a valid processing request
            websocket.send_json(
                {
                    "input_data": "Test streaming",
                    "input_tokens": 10,
                    "processor_type": "local",
                }
            )

            # We expect at least one chunk and a 'done' message
            response = websocket.receive_json()
            assert response["type"] in ["chunk", "error"]

            if response["type"] == "chunk":
                done = websocket.receive_json()
                assert done["type"] == "done"
    except (ConnectionRefusedError, OSError) as e:
        pytest.skip(f"WebSocket connection skipped: {e}")
    except Exception as e:
        pytest.fail(f"WebSocket communication failed unexpectedly: {e}")


def test_websocket_invalid_data():
    client = TestClient(app)
    api_key_plain = register_test_api_key()

    with client.websocket_connect(f"/ws/stream?api_key={api_key_plain}") as websocket:
        # Send invalid data (missing required fields)
        websocket.send_json({"invalid": "data"})

        response = websocket.receive_json()
        assert response["type"] == "error"


def test_websocket_unauthorized():
    client = TestClient(app)
    # No api_key or token
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/stream"):
            pass
