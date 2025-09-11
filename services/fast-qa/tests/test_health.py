"""
Tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "Fast Q&A Service"
    assert "version" in data["data"]
    assert "timestamp" in data["data"]
    assert data["error"] is None


def test_health_detailed(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "Fast Q&A Service"
    assert "checks" in data["data"]
    assert "database" in data["data"]["checks"]
    assert data["error"] is None


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["service"] == "Fast Q&A Service"
    assert "version" in data["data"]
    assert "environment" in data["data"]
    assert data["error"] is None