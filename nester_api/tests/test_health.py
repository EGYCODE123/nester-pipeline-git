"""
Tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from nester_api.app.main import create_app


@pytest.fixture
def app():
    """Create test app."""
    import os
    os.environ["API_KEY"] = "test-key"
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_health_live(client):
    """Test liveness endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_ready(client):
    """Test readiness endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_no_auth_required(client):
    """Test that health endpoints don't require authentication."""
    # Test without auth headers
    response_live = client.get("/health/live")
    response_ready = client.get("/health/ready")
    
    assert response_live.status_code == 200
    assert response_ready.status_code == 200



