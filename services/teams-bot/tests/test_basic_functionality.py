"""
Basic functionality tests for Teams Bot Service.
Tests core components, configuration, and Bot Framework integration.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.adapters.teams_adapter import TeamsAdapter
from bot.conversation import ConversationManager, UserProfile
from bot.teams_bot import TeamsBot
from config.settings import TeamsConfig


class TestTeamsConfig:
    """Test Teams service configuration."""
    
    def test_config_initialization(self):
        """Test that configuration initializes with required fields."""
        # Mock environment variables for testing
        config = TeamsConfig(
            DATABASE_URL="postgresql://test:test@localhost/test",
            TEAMS_BOT_APP_ID="test-app-id",
            TEAMS_BOT_APP_PASSWORD="test-password",
            TEAMS_BOT_WEBHOOK_URL="https://test.example.com/webhook",
            QUERY_ORCHESTRATION_URL="http://localhost:8001",
            USER_CONTEXT_URL="http://localhost:8002",
            ENVIRONMENT="development"
        )
        
        assert config.SERVICE_NAME == "teams-bot"
        assert config.SERVICE_VERSION == "1.2.0"
        assert config.ENVIRONMENT == "development"
        assert config.TEAMS_BOT_APP_ID == "test-app-id"
    
    def test_environment_detection(self):
        """Test environment detection methods."""
        config = TeamsConfig(
            DATABASE_URL="postgresql://test:test@localhost/test",
            TEAMS_BOT_APP_ID="test-app-id",
            TEAMS_BOT_APP_PASSWORD="test-password",
            TEAMS_BOT_WEBHOOK_URL="https://test.example.com/webhook",
            QUERY_ORCHESTRATION_URL="http://localhost:8001",
            USER_CONTEXT_URL="http://localhost:8002",
            ENVIRONMENT="development"
        )
        
        assert config.is_development() is True
        assert config.is_production() is False


class TestConversationManager:
    """Test conversation state management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.conversation_manager = ConversationManager()
    
    def test_create_user_profile(self):
        """Test user profile creation."""
        profile = self.conversation_manager.create_user_profile(
            teams_user_id="user123",
            teams_tenant_id="tenant456",
            display_name="Test User",
            skill_level="diy_enthusiast"
        )
        
        assert isinstance(profile, UserProfile)
        assert profile.teams_user_id == "user123"
        assert profile.teams_tenant_id == "tenant456"
        assert profile.display_name == "Test User"
        assert profile.skill_level == "diy_enthusiast"
        assert isinstance(profile.preferences, dict)
    
    def test_create_conversation_data(self):
        """Test conversation data creation."""
        user_profile = self.conversation_manager.create_user_profile(
            teams_user_id="user123",
            teams_tenant_id="tenant456",
            display_name="Test User"
        )
        
        conversation_data = self.conversation_manager.create_conversation_data(
            session_id="session123",
            user_profile=user_profile
        )
        
        assert conversation_data.session_id == "session123"
        assert conversation_data.user_profile == user_profile
        assert isinstance(conversation_data.conversation_history, list)
        assert isinstance(conversation_data.troubleshooting_context, dict)
    
    def test_add_message_to_history(self):
        """Test adding messages to conversation history."""
        conversation_data = self.conversation_manager.create_conversation_data("session123")
        
        self.conversation_manager.add_message_to_history(
            conversation_data,
            message_type="user",
            content="My washer won't start",
            timestamp="2025-09-08T10:00:00Z"
        )
        
        assert len(conversation_data.conversation_history) == 1
        message = conversation_data.conversation_history[0]
        assert message["type"] == "user"
        assert message["content"] == "My washer won't start"
        assert message["timestamp"] == "2025-09-08T10:00:00Z"
        assert conversation_data.last_activity_timestamp == "2025-09-08T10:00:00Z"


@pytest.mark.asyncio
class TestTeamsBot:
    """Test Teams bot functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock state accessors
        self.conversation_state_accessor = AsyncMock()
        self.user_state_accessor = AsyncMock()
        
        # Create bot instance
        self.bot = TeamsBot(
            conversation_state_accessor=self.conversation_state_accessor,
            user_state_accessor=self.user_state_accessor
        )
    
    async def test_welcome_message_generation(self):
        """Test welcome message generation."""
        welcome_message = await self.bot._generate_welcome_message("Test User")
        
        assert "Hello Test User!" in welcome_message
        assert "washing machine troubleshooting" in welcome_message
        assert "help" in welcome_message.lower()
    
    async def test_help_response_generation(self):
        """Test help response generation."""
        help_response = await self.bot._generate_help_response()
        
        assert "help" in help_response.lower()
        assert "commands" in help_response.lower()
        assert "washing machine" in help_response.lower()
    
    async def test_greeting_response_generation(self):
        """Test greeting response generation."""
        greeting_response = await self.bot._generate_greeting_response("Test User")
        
        assert "Hello Test User!" in greeting_response
        assert "troubleshooting" in greeting_response.lower()
    
    async def test_clarification_response_generation(self):
        """Test clarification response generation."""
        clarification_response = await self.bot._generate_clarification_response()
        
        assert "details" in clarification_response.lower()
        assert "washing machine" in clarification_response.lower()


class TestTeamsAdapter:
    """Test Teams Bot Framework adapter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock configuration for testing
        self.adapter = TeamsAdapter()
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        assert self.adapter.adapter is not None
        assert self.adapter.conversation_state is not None
        assert self.adapter.user_state is not None
        assert self.adapter.memory_storage is not None
    
    def test_state_accessors_creation(self):
        """Test state accessor creation."""
        conversation_accessor = self.adapter.get_conversation_state_accessor("test_property")
        user_accessor = self.adapter.get_user_state_accessor("test_property")
        
        assert conversation_accessor is not None
        assert user_accessor is not None


if __name__ == "__main__":
    pytest.main([__file__])