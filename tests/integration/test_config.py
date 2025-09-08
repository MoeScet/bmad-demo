"""
Integration tests for configuration management across services.
"""
import os
import sys
from pathlib import Path

import pytest

# Add shared modules to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "shared" / "python"))


class TestConfigurationIntegration:
    """Test configuration loading and validation across different environments."""
    
    def test_base_config_loading(self):
        """Test base configuration can be loaded with minimal settings."""
        # Set required environment variables
        os.environ.update({
            "SERVICE_NAME": "test-service",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db"
        })
        
        from config.base import BaseConfig, load_config
        
        config = load_config(BaseConfig)
        
        assert config.SERVICE_NAME == "test-service"
        assert config.DATABASE_URL.startswith("postgresql")
        assert config.ENVIRONMENT in ["development", "staging", "production", "test"]
    
    def test_teams_config_validation(self):
        """Test Teams-specific configuration validation."""
        os.environ.update({
            "SERVICE_NAME": "teams-bot",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
            "TEAMS_BOT_APP_ID": "12345678-1234-1234-1234-123456789012",
            "TEAMS_BOT_APP_PASSWORD": "test-password",
            "TEAMS_BOT_TENANT_ID": "87654321-4321-4321-4321-210987654321"
        })
        
        from config.base import TeamsConfig, load_config
        
        config = load_config(TeamsConfig)
        
        assert config.TEAMS_BOT_APP_ID == "12345678-1234-1234-1234-123456789012"
        assert config.TEAMS_BOT_APP_PASSWORD == "test-password"
        assert config.TEAMS_BOT_TENANT_ID == "87654321-4321-4321-4321-210987654321"
    
    def test_invalid_database_url_raises_error(self):
        """Test that invalid database URL raises validation error."""
        os.environ.update({
            "SERVICE_NAME": "test-service",
            "DATABASE_URL": "invalid://url"
        })
        
        from config.base import BaseConfig, load_config
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            load_config(BaseConfig)
    
    def test_timeout_configuration(self):
        """Test service timeout configuration."""
        os.environ.update({
            "SERVICE_NAME": "query-orchestration",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
            "FAST_QA_TIMEOUT": "3.0",
            "SEMANTIC_SEARCH_TIMEOUT": "12.0",
            "SAFETY_CLASSIFICATION_TIMEOUT": "1.0",
            "USER_CONTEXT_TIMEOUT": "0.5"
        })
        
        from config.base import ServiceTimeoutConfig, load_config
        
        config = load_config(ServiceTimeoutConfig)
        
        assert config.FAST_QA_TIMEOUT == 3.0
        assert config.SEMANTIC_SEARCH_TIMEOUT == 12.0
        assert config.SAFETY_CLASSIFICATION_TIMEOUT == 1.0
        assert config.USER_CONTEXT_TIMEOUT == 0.5


class TestLoggingIntegration:
    """Test logging configuration integration."""
    
    def test_logging_configuration(self):
        """Test logging can be configured for different environments."""
        from utils.logging import configure_logging
        
        # Test development configuration
        logger = configure_logging(
            service_name="test-service",
            service_version="1.0.0",
            log_level="DEBUG",
            log_format="text",
            environment="development"
        )
        
        assert logger is not None
        
        # Test that logging works
        logger.info("Test log message", test_field="test_value")
    
    def test_correlation_id_context(self):
        """Test correlation ID context management."""
        from utils.logging import set_correlation_id, get_correlation_id, clear_correlation_id
        
        # Initially no correlation ID
        assert get_correlation_id() is None
        
        # Set correlation ID
        test_id = "test-123"
        set_id = set_correlation_id(test_id)
        assert set_id == test_id
        assert get_correlation_id() == test_id
        
        # Generate new correlation ID
        generated_id = set_correlation_id()
        assert generated_id != test_id
        assert get_correlation_id() == generated_id
        
        # Clear correlation ID
        clear_correlation_id()
        assert get_correlation_id() is None