"""Tests for FastAPI endpoints."""

import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from nester.api.app import app

# Set test API token
TEST_TOKEN = "test_token_123"


def test_health():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "version" in data


@patch('nester.api.app.API_TOKEN', TEST_TOKEN)
def test_efficiency_happy(monkeypatch):
    """Test efficiency endpoint with valid request."""
    # Set API token via environment
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    
    client = TestClient(app)
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["quote_id"] == "Q-1"
    assert "results" in data
    assert len(data["results"]) == 1
    assert "waste_factor_pct" in data["results"][0]
    assert "totals" in data
    assert "eff_pct" in data["totals"]
    assert "waste_pct" in data["totals"]
    assert "calc_id" in data
    assert "version" in data


@patch('nester.api.app.API_TOKEN', TEST_TOKEN)
def test_efficiency_with_candidate_widths(monkeypatch):
    """Test efficiency endpoint with available_widths_mm."""
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    
    client = TestClient(app)
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "available_widths_mm": [1900, 2050, 2400],
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1


@patch('nester.api.app.API_TOKEN', TEST_TOKEN)
def test_available_widths_validation(monkeypatch):
    """Test that negative or zero widths in available_widths_mm are rejected."""
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    
    client = TestClient(app)
    
    # Negative width
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "available_widths_mm": [-100, 2400],
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 422  # Validation error
    
    # Zero width
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "available_widths_mm": [0, 2400],
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 422  # Validation error


def test_auth_required():
    """Test that authentication is required."""
    client = TestClient(app)
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    
    # No authorization header
    response = client.post("/api/v1/waste/efficiency", json=body)
    assert response.status_code == 401
    
    # Invalid token
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


@patch('nester.api.app.API_TOKEN', TEST_TOKEN)
def test_invalid_payload(monkeypatch):
    """Test efficiency endpoint with invalid payload."""
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    
    client = TestClient(app)
    
    # Invalid model
    body = {
        "quote_id": "Q-1",
        "model": "invalid",
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 422  # Validation error
    
    # Zero width
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "lines": [
            {
                "line_id": "L1",
                "width_mm": 0,
                "drop_mm": 2100,
                "qty": 2
            }
        ]
    }
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 422  # Validation error


@patch('nester.api.app.API_TOKEN', TEST_TOKEN)
def test_too_many_lines(monkeypatch):
    """Test that requests with >1000 lines are rejected."""
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    
    client = TestClient(app)
    body = {
        "quote_id": "Q-1",
        "model": "blinds",
        "lines": [
            {
                "line_id": f"L{i}",
                "width_mm": 2400,
                "drop_mm": 2100,
                "qty": 1
            }
            for i in range(1001)
        ]
    }
    
    response = client.post(
        "/api/v1/waste/efficiency",
        json=body,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data.get("detail", {})
    assert "1000 lines" in str(data.get("detail", {})).lower()

