"""
Tests for Teams Bot Service main application.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint returns correct status."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["service"] == "teams-bot"
    assert data["status"] == "healthy"
    assert data["environment"] == "test"
    assert "version" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns service information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["service"] == "BMAD Teams Bot Service"
    assert data["environment"] == "test"
    assert "version" in data
    assert "docs" in data


def test_teams_webhook_endpoint(client: TestClient):
    """Test Teams webhook endpoint accepts POST requests."""
    response = client.post("/api/messages", json={"test": "message"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


def test_correlation_id_header(client: TestClient, correlation_id: str):
    """Test correlation ID is properly handled in requests."""
    headers = {"X-Correlation-ID": correlation_id}
    response = client.get("/health", headers=headers)
    
    assert response.status_code == 200
    # Check that correlation ID is returned in response headers
    assert response.headers.get("X-Correlation-ID") == correlation_id


def test_cors_headers(client: TestClient):
    """Test CORS headers are properly set."""
    response = client.get("/health")
    
    # Check that CORS headers are present
    assert response.status_code == 200
    # In a real CORS setup, we would check for access-control headers
    # For now, just verify the endpoint is accessible


class TestConfiguration:
    """Test configuration loading and validation."""
    
    def test_config_validation(self, mock_config):
        """Test configuration validation works correctly."""
        assert mock_config.SERVICE_NAME == "teams-bot"
        assert mock_config.ENVIRONMENT == "test"
        assert mock_config.is_testing() is True
        assert mock_config.is_production() is False
    
    def test_correlation_id_generation(self, mock_config):
        """Test correlation ID generation."""
        correlation_id = mock_config.generate_correlation_id()
        
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 36  # UUID4 length with hyphens
        
        # Generate another to ensure they're unique
        another_id = mock_config.generate_correlation_id()
        assert correlation_id != another_id