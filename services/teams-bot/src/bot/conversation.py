"""
Conversation State Management for Teams Bot
Handles conversation context, user preferences, and session tracking.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

# Setup structured logging
logger = structlog.get_logger(__name__)


@dataclass
class UserProfile:
    """User profile information from Teams and user context."""
    teams_user_id: str
    teams_tenant_id: str
    display_name: str
    email: Optional[str] = None
    skill_level: str = "novice"  # novice, diy_enthusiast, renter
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class ConversationData:
    """Conversation state data for Teams bot interactions."""
    session_id: str
    user_profile: Optional[UserProfile] = None
    conversation_history: List[Dict[str, Any]] = None
    current_query: Optional[str] = None
    search_strategy: Optional[str] = None
    troubleshooting_context: Dict[str, Any] = None
    last_activity_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.troubleshooting_context is None:
            self.troubleshooting_context = {}


class ConversationManager:
    """
    Manages conversation state and context for Teams bot interactions.
    
    Provides methods for updating conversation state, tracking user context,
    and managing troubleshooting session data.
    """
    
    def __init__(self):
        """Initialize conversation manager."""
        self.logger = structlog.get_logger(__name__)
    
    def create_user_profile(
        self,
        teams_user_id: str,
        teams_tenant_id: str,
        display_name: str,
        email: Optional[str] = None,
        skill_level: str = "novice"
    ) -> UserProfile:
        """
        Create a new user profile from Teams user information.
        
        Args:
            teams_user_id: Teams user ID
            teams_tenant_id: Teams tenant ID
            display_name: User's display name from Teams
            email: User's email address (optional)
            skill_level: User skill level for troubleshooting
            
        Returns:
            UserProfile instance
        """
        profile = UserProfile(
            teams_user_id=teams_user_id,
            teams_tenant_id=teams_tenant_id,
            display_name=display_name,
            email=email,
            skill_level=skill_level
        )
        
        self.logger.info(
            "User profile created",
            service="teams-bot",
            teams_user_id=teams_user_id,
            display_name=display_name,
            skill_level=skill_level
        )
        
        return profile
    
    def create_conversation_data(
        self,
        session_id: str,
        user_profile: Optional[UserProfile] = None
    ) -> ConversationData:
        """
        Create new conversation data for a Teams conversation.
        
        Args:
            session_id: Unique session identifier
            user_profile: User profile information
            
        Returns:
            ConversationData instance
        """
        conversation_data = ConversationData(
            session_id=session_id,
            user_profile=user_profile
        )
        
        self.logger.info(
            "Conversation data created",
            service="teams-bot",
            session_id=session_id,
            has_user_profile=user_profile is not None
        )
        
        return conversation_data
    
    def add_message_to_history(
        self,
        conversation_data: ConversationData,
        message_type: str,
        content: str,
        timestamp: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation history.
        
        Args:
            conversation_data: Conversation data to update
            message_type: Type of message (user, bot, system)
            content: Message content
            timestamp: Message timestamp
            metadata: Optional metadata for the message
        """
        if metadata is None:
            metadata = {}
        
        message_entry = {
            "type": message_type,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata
        }
        
        conversation_data.conversation_history.append(message_entry)
        conversation_data.last_activity_timestamp = timestamp
        
        self.logger.debug(
            "Message added to conversation history",
            service="teams-bot",
            session_id=conversation_data.session_id,
            message_type=message_type,
            history_length=len(conversation_data.conversation_history)
        )
    
    def update_troubleshooting_context(
        self,
        conversation_data: ConversationData,
        context_key: str,
        context_value: Any
    ) -> None:
        """
        Update troubleshooting context with new information.
        
        Args:
            conversation_data: Conversation data to update
            context_key: Context key to update
            context_value: New context value
        """
        conversation_data.troubleshooting_context[context_key] = context_value
        
        self.logger.debug(
            "Troubleshooting context updated",
            service="teams-bot",
            session_id=conversation_data.session_id,
            context_key=context_key
        )
    
    def get_conversation_summary(self, conversation_data: ConversationData) -> Dict[str, Any]:
        """
        Get a summary of the conversation state.
        
        Args:
            conversation_data: Conversation data to summarize
            
        Returns:
            Dictionary with conversation summary
        """
        return {
            "session_id": conversation_data.session_id,
            "user_display_name": conversation_data.user_profile.display_name if conversation_data.user_profile else None,
            "skill_level": conversation_data.user_profile.skill_level if conversation_data.user_profile else None,
            "message_count": len(conversation_data.conversation_history),
            "current_query": conversation_data.current_query,
            "search_strategy": conversation_data.search_strategy,
            "last_activity": conversation_data.last_activity_timestamp,
            "troubleshooting_context_keys": list(conversation_data.troubleshooting_context.keys())
        }