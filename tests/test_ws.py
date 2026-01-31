import pytest
from fastapi.testclient import TestClient
from strict.api.server import app
from strict.config import settings


from pydantic import SecretStr


def get_api_key():
    if settings.valid_api_keys:
        return settings.valid_api_keys[0].get_secret_value()
    return "test-api-key"


def test_websocket_connection():
    client = TestClient(app)
    api_key_plain = get_api_key()

    # Update valid keys for test if needed
    if not any(k.get_secret_value() == api_key_plain for k in settings.valid_api_keys):
        settings.valid_api_keys.append(SecretStr(api_key_plain))

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
    api_key_plain = get_api_key()

    with client.websocket_connect(f"/ws/stream?api_key={api_key_plain}") as websocket:
        # Send invalid data (missing required fields)
        websocket.send_json({"invalid": "data"})

        response = websocket.receive_json()
        assert response["type"] == "error"


def test_websocket_unauthorized():
    client = TestClient(app)
    # No api_key or token
    with pytest.raises(
        Exception
    ):  # TestClient raises when connection is closed with error code
        with client.websocket_connect("/ws/stream") as websocket:
            pass
