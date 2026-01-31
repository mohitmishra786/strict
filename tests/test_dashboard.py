"""Tests for web dashboard."""

from fastapi.testclient import TestClient

from strict.api.server import app


def test_dashboard_home():
    """Test dashboard home page loads."""
    client = TestClient(app)
    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert "html" in response.headers["content-type"]


def test_dashboard_api_docs():
    """Test API docs endpoint."""
    client = TestClient(app)
    response = client.get("/dashboard/api/docs")

    assert response.status_code == 200
    data = response.json()
    assert "swagger" in data
    assert "redoc" in data
    assert "openapi" in data


def test_dashboard_has_content():
    """Test dashboard page contains expected content."""
    client = TestClient(app)
    response = client.get("/dashboard/")

    content = response.text
    assert "Strict Dashboard" in content
    assert "Configuration" in content
    assert "API Endpoints" in content
