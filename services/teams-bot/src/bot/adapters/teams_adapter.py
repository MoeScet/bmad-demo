"""
Microsoft Teams Bot Framework Adapter
Bot Framework adapter configuration for Microsoft Teams integration.
"""
from __future__ import annotations

import uuid
from typing import Callable, Optional

import structlog
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState
)
from botbuilder.schema import Activity

from config.settings import teams_config

# Setup structured logging
logger = structlog.get_logger(__name__)


class TeamsAdapter:
    """
    Microsoft Teams Bot Framework adapter with conversation state management.
    
    Handles Bot Framework authentication, middleware, and state management
    for Teams conversations and user interactions.
    """
    
    def __init__(self):
        """Initialize Teams adapter with Bot Framework settings."""
        self.correlation_id = str(uuid.uuid4())
        
        # Bot Framework adapter settings
        self.settings = BotFrameworkAdapterSettings(
            app_id=teams_config.TEAMS_BOT_APP_ID,
            app_password=teams_config.TEAMS_BOT_APP_PASSWORD
        )
        
        # Create Bot Framework adapter
        self.adapter = BotFrameworkAdapter(self.settings)
        
        # Setup conversation state management
        # Note: In production, replace MemoryStorage with persistent storage
        self.memory_storage = MemoryStorage()
        self.conversation_state = ConversationState(self.memory_storage)
        self.user_state = UserState(self.memory_storage)
        
        # Add state middleware to adapter
        #self.adapter.use(self.conversation_state)
        #self.adapter.use(self.user_state)
        
        logger.info(
            "Teams adapter initialized",
            correlation_id=self.correlation_id,
            service="teams-bot",
            app_id_configured=bool(teams_config.TEAMS_BOT_APP_ID),
            storage_type="memory"
        )
    
    async def process_activity(
        self, 
        auth_header: str, 
        activity_data: dict,
        bot_handler: Callable[[TurnContext], None]
    ) -> str:
        """
        Process incoming activity through Bot Framework adapter.
        
        Args:
            auth_header: Authorization header from Teams webhook
            activity_data: Raw activity data from Teams
            bot_handler: Bot logic handler function
            
        Returns:
            Response body for Teams webhook
        """
        correlation_id = str(uuid.uuid4())
        
        try:
            logger.info(
                "Processing Teams activity",
                correlation_id=correlation_id,
                service="teams-bot",
                activity_type=activity_data.get("type", "unknown"),
                conversation_id=activity_data.get("conversation", {}).get("id")
            )
            
            # Create activity from data
            activity = Activity().deserialize(activity_data)
            
            # Process through Bot Framework adapter
            response = await self.adapter.process_activity(
                activity,
                auth_header,
                bot_handler
            )
            
            logger.info(
                "Activity processed successfully",
                correlation_id=correlation_id,
                service="teams-bot",
                response_status="success"
            )
            
            return response or ""
            
        except Exception as error:
            logger.error(
                "Activity processing failed",
                correlation_id=correlation_id,
                service="teams-bot",
                error=str(error),
                error_type=type(error).__name__
            )
            raise
    
    async def save_conversation_state(self, turn_context: TurnContext) -> None:
        """Save conversation and user state after processing."""
        try:
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)
            
            logger.debug(
                "Conversation state saved",
                service="teams-bot",
                conversation_id=turn_context.activity.conversation.id
            )
            
        except Exception as error:
            logger.error(
                "Failed to save conversation state",
                service="teams-bot",
                error=str(error),
                error_type=type(error).__name__,
                conversation_id=turn_context.activity.conversation.id
            )
            raise
    
    def get_conversation_state_accessor(self, property_name: str):
        """Get conversation state property accessor."""
        return self.conversation_state.create_property(property_name)
    
    def get_user_state_accessor(self, property_name: str):
        """Get user state property accessor."""
        return self.user_state.create_property(property_name)