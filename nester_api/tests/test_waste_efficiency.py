"""
Tests for waste efficiency endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from nester_api.app.main import create_app
from nester_api.app.core.config import Settings


# Test API key
TEST_API_KEY = "test-api-key-12345"


@pytest.fixture
def app():
    """Create test app with test settings."""
    # Override settings for testing
    import os
    os.environ["API_KEY"] = TEST_API_KEY
    os.environ["API_LOG_LEVEL"] = "debug"
    
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return authentication headers."""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}


@pytest.fixture
def sample_request():
    """Sample request body matching the API contract."""
    return {
        "quote_id": "Q-TEST-001",
        "model": "blinds",
        "available_widths_mm": [1900, 2050, 2400, 3000],
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2300,
                "drop_mm": 2100,
                "qty": 2,
                "fabric_code": "FAB001",
                "series": "SERIES-A"
            }
        ]
    }


def test_efficiency_valid_request(client, auth_headers, sample_request):
    """Test valid request with authentication."""
    response = client.post(
        "/api/v1/waste/efficiency",
        json=sample_request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "calc_id" in data
    assert data["quote_id"] == "Q-TEST-001"
    assert "results" in data
    assert "totals" in data
    assert data["version"] == "1.0.0"
    assert data["message"] == "ok"
    
    # Verify results structure
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["line_id"] == "L1"
    assert "waste_factor_pct" in result
    assert "utilization" in result
    assert "used_length_mm" in result
    
    # Verify totals structure
    totals = data["totals"]
    assert "eff_pct" in totals
    assert "waste_pct" in totals
    assert "total_area_m2" in totals
    
    # Verify correlation ID in headers
    assert "X-Correlation-ID" in response.headers


def test_efficiency_missing_auth(client, sample_request):
    """Test request without authentication."""
    response = client.post(
        "/api/v1/waste/efficiency",
        json=sample_request
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"] == "unauthorized"


def test_efficiency_invalid_token(client, sample_request):
    """Test request with invalid token."""
    response = client.post(
        "/api/v1/waste/efficiency",
        json=sample_request,
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"] == "unauthorized"


def test_efficiency_invalid_payload(client, auth_headers):
    """Test request with invalid payload."""
    invalid_request = {
        "quote_id": "Q-TEST-001",
        "model": "invalid_model",  # Invalid model
        "lines": []
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=invalid_request,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_efficiency_empty_lines(client, auth_headers):
    """Test request with empty lines list."""
    request = {
        "quote_id": "Q-TEST-001",
        "model": "blinds",
        "available_widths_mm": [3000],
        "lines": []
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["totals"]["eff_pct"] == 0.0


def test_efficiency_too_many_lines(client, auth_headers):
    """Test request exceeding line limit."""
    request = {
        "quote_id": "Q-TEST-001",
        "model": "blinds",
        "available_widths_mm": [3000],
        "lines": [
            {
                "line_id": f"L{i}",
                "width_mm": 1000,
                "drop_mm": 1000,
                "qty": 1
            }
            for i in range(1001)  # Exceeds 1000 limit
        ]
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=request,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "bad_request" in data["detail"]["error"]


def test_efficiency_correlation_id(client, auth_headers, sample_request):
    """Test that correlation ID is generated and returned."""
    response = client.post(
        "/api/v1/waste/efficiency",
        json=sample_request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    corr_id = response.headers["X-Correlation-ID"]
    assert len(corr_id) > 0


def test_efficiency_custom_correlation_id(client, auth_headers, sample_request):
    """Test that custom correlation ID is preserved."""
    custom_corr_id = "custom-correlation-id-12345"
    headers = {**auth_headers, "X-Correlation-ID": custom_corr_id}
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=sample_request,
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_corr_id



