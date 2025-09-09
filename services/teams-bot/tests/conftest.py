"""
Test configuration and fixtures for Teams Bot Service.
"""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root and shared modules to path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root / "shared" / "python"))
sys.path.insert(0, str(project_root / "services" / "teams-bot" / "src"))

# Set test environment variables
os.environ.update({
    "ENVIRONMENT": "test",
    "SERVICE_NAME": "teams-bot",
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/bmad_test",
    "TEAMS_BOT_APP_ID": "00000000-0000-0000-0000-000000000000",
    "TEAMS_BOT_APP_PASSWORD": "test-password",
    "TEAMS_BOT_TENANT_ID": "00000000-0000-0000-0000-000000000000",
    "LOG_LEVEL": "ERROR",  # Reduce log noise in tests
})


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    from main import app
    return TestClient(app)


@pytest.fixture
def correlation_id():
    """Generate test correlation ID."""
    return "test-correlation-id-123"


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from config.settings import TeamsConfig
    return TeamsConfig(
        SERVICE_NAME="teams-bot",
        SERVICE_VERSION="test",
        ENVIRONMENT="test",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/bmad_test",
        TEAMS_BOT_APP_ID="00000000-0000-0000-0000-000000000000",
        TEAMS_BOT_APP_PASSWORD="test-password",
        TEAMS_BOT_WEBHOOK_URL="https://test.example.com/webhook",
        QUERY_ORCHESTRATION_URL="http://localhost:8001",
        USER_CONTEXT_URL="http://localhost:8002",
    )