"""
Microsoft Teams Bot Implementation
Main bot logic for handling Teams conversations and troubleshooting queries.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

import structlog
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

from bot.conversation import ConversationData, ConversationManager, UserProfile
from config.settings import teams_config

# Setup structured logging
logger = structlog.get_logger(__name__)


class TeamsBot(ActivityHandler):
    """
    Microsoft Teams Bot for washing machine troubleshooting assistance.
    
    Handles Teams conversations, user greetings, help commands,
    and basic query processing with conversation state management.
    """
    
    def __init__(self, conversation_state_accessor, user_state_accessor):
        """
        Initialize Teams bot with state accessors.
        
        Args:
            conversation_state_accessor: Bot Framework conversation state accessor
            user_state_accessor: Bot Framework user state accessor
        """
        super().__init__()
        
        self.conversation_state_accessor = conversation_state_accessor
        self.user_state_accessor = user_state_accessor
        self.conversation_manager = ConversationManager()
        
        logger.info(
            "Teams bot initialized",
            service="teams-bot",
            version=teams_config.SERVICE_VERSION
        )
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """
        Handle incoming message activities from Teams users.
        
        Args:
            turn_context: Bot Framework turn context for the conversation
        """
        correlation_id = str(uuid.uuid4())
        user_message = turn_context.activity.text.strip() if turn_context.activity.text else ""
        
        logger.info(
            "Processing user message",
            correlation_id=correlation_id,
            service="teams-bot",
            user_id=turn_context.activity.from_property.id,
            conversation_id=turn_context.activity.conversation.id,
            message_length=len(user_message),
            conversation_type=turn_context.activity.conversation.conversation_type
        )
        
        try:
            # Get conversation state
            conversation_data = await self._get_conversation_data(turn_context)
            
            # Process user message and generate response
            response_text = await self._process_user_message(
                user_message, 
                conversation_data, 
                turn_context,
                correlation_id
            )
            
            # Send response to user
            response_activity = MessageFactory.text(response_text)
            await turn_context.send_activity(response_activity)
            
            # Update conversation history
            timestamp = datetime.utcnow().isoformat()
            self.conversation_manager.add_message_to_history(
                conversation_data,
                "user",
                user_message,
                timestamp
            )
            self.conversation_manager.add_message_to_history(
                conversation_data,
                "bot",
                response_text,
                timestamp
            )
            
            # Save updated conversation state
            await self.conversation_state_accessor.set(turn_context, conversation_data)
            
            logger.info(
                "Message processed successfully",
                correlation_id=correlation_id,
                service="teams-bot",
                response_length=len(response_text)
            )
            
        except Exception as error:
            logger.error(
                "Message processing failed",
                correlation_id=correlation_id,
                service="teams-bot",
                error=str(error),
                error_type=type(error).__name__,
                user_id=turn_context.activity.from_property.id
            )
            
            # Send error response to user
            error_response = "I'm sorry, I encountered an issue processing your message. Please try again."
            await turn_context.send_activity(MessageFactory.text(error_response))
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ) -> None:
        """
        Handle members added to conversation (greeting new users).
        
        Args:
            members_added: List of members added to the conversation
            turn_context: Bot Framework turn context for the conversation
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            "Members added to conversation",
            correlation_id=correlation_id,
            service="teams-bot",
            members_count=len(members_added),
            conversation_id=turn_context.activity.conversation.id
        )
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Don't greet the bot itself
                welcome_message = await self._generate_welcome_message(member.name or "there")
                await turn_context.send_activity(MessageFactory.text(welcome_message))
                
                logger.info(
                    "Welcome message sent",
                    correlation_id=correlation_id,
                    service="teams-bot",
                    member_id=member.id,
                    member_name=member.name
                )
    
    async def _get_conversation_data(self, turn_context: TurnContext) -> ConversationData:
        """
        Get or create conversation data for the current conversation.
        
        Args:
            turn_context: Bot Framework turn context
            
        Returns:
            ConversationData instance for the conversation
        """
        conversation_data = await self.conversation_state_accessor.get(
            turn_context, 
            lambda: None
        )
        
        if conversation_data is None:
            # Create new conversation data
            session_id = str(uuid.uuid4())
            user_profile = await self._create_user_profile_from_activity(turn_context.activity)
            
            conversation_data = self.conversation_manager.create_conversation_data(
                session_id=session_id,
                user_profile=user_profile
            )
            
            logger.info(
                "New conversation data created",
                service="teams-bot",
                session_id=session_id,
                user_id=turn_context.activity.from_property.id,
                conversation_id=turn_context.activity.conversation.id
            )
        
        return conversation_data
    
    async def _create_user_profile_from_activity(self, activity: Activity) -> UserProfile:
        """
        Create user profile from Teams activity information.
        
        Args:
            activity: Teams activity containing user information
            
        Returns:
            UserProfile instance
        """
        teams_user_id = activity.from_property.id
        teams_tenant_id = activity.conversation.tenant_id if hasattr(activity.conversation, 'tenant_id') else ""
        display_name = activity.from_property.name or "Teams User"
        
        # TODO: Extract email from Teams user information if available
        # This will be enhanced when SSO authentication is implemented
        
        return self.conversation_manager.create_user_profile(
            teams_user_id=teams_user_id,
            teams_tenant_id=teams_tenant_id,
            display_name=display_name,
            skill_level="novice"  # Default skill level
        )
    
    async def _process_user_message(
        self, 
        message: str, 
        conversation_data: ConversationData,
        turn_context: TurnContext,
        correlation_id: str
    ) -> str:
        """
        Process user message and generate appropriate response.
        
        Args:
            message: User's message text
            conversation_data: Current conversation state
            turn_context: Bot Framework turn context
            correlation_id: Request correlation ID
            
        Returns:
            Bot response text
        """
        message_lower = message.lower().strip()
        
        # Handle help commands
        if message_lower in ["help", "/help", "?", "commands"]:
            return await self._generate_help_response()
        
        # Handle greeting messages
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            user_name = conversation_data.user_profile.display_name if conversation_data.user_profile else "there"
            return await self._generate_greeting_response(user_name)
        
        # Handle basic troubleshooting query
        if len(message) > 10:  # Assume messages longer than 10 chars are queries
            conversation_data.current_query = message
            return await self._generate_query_response(message, conversation_data, correlation_id)
        
        # Default response for unclear messages
        return await self._generate_clarification_response()
    
    async def _generate_welcome_message(self, user_name: str) -> str:
        """
        Generate welcome message for new users.
        
        Args:
            user_name: Name of the user being welcomed
            
        Returns:
            Welcome message text
        """
        return f"""Hello {user_name}! 👋

I'm your washing machine troubleshooting assistant. I can help you diagnose and fix issues with your washing machine.

**How I can help:**
• Troubleshoot common washing machine problems
• Provide step-by-step repair guidance
• Answer questions about washing machine maintenance

**To get started:**
• Describe your washing machine issue
• Type "help" for available commands
• Just ask me any question about your washer

What washing machine issue can I help you with today?"""
    
    async def _generate_help_response(self) -> str:
        """
        Generate help response with available commands.
        
        Returns:
            Help message text
        """
        return """🔧 **Washing Machine Troubleshooting Assistant**

**Available Commands:**
• `help` - Show this help message
• `hello` - Get a greeting and introduction

**How to use:**
• Simply describe your washing machine problem
• Ask questions about repairs or maintenance
• I'll provide step-by-step troubleshooting guidance

**Example queries:**
• "My washer won't start"
• "Water is leaking from the bottom"
• "The drum isn't spinning"
• "Strange noise during wash cycle"

Just describe your issue and I'll help you troubleshoot it! 🧽"""
    
    async def _generate_greeting_response(self, user_name: str) -> str:
        """
        Generate greeting response for returning users.
        
        Args:
            user_name: Name of the user
            
        Returns:
            Greeting message text
        """
        return f"""Hello {user_name}! 👋

I'm here to help with your washing machine troubleshooting needs. 

What issue can I help you diagnose today? Just describe what's happening with your washer and I'll guide you through the troubleshooting process."""
    
    async def _generate_query_response(
        self, 
        query: str, 
        conversation_data: ConversationData,
        correlation_id: str
    ) -> str:
        """
        Generate response to user troubleshooting query.
        
        Args:
            query: User's troubleshooting query
            conversation_data: Current conversation state
            correlation_id: Request correlation ID
            
        Returns:
            Query response text
        """
        logger.info(
            "Processing troubleshooting query",
            correlation_id=correlation_id,
            service="teams-bot",
            query_length=len(query),
            session_id=conversation_data.session_id
        )
        
        # TODO: In future stories, this will integrate with Query Orchestration Service
        # For now, provide a basic acknowledgment response
        
        # Update troubleshooting context
        self.conversation_manager.update_troubleshooting_context(
            conversation_data,
            "last_query",
            query
        )
        
        return f"""Thank you for describing your washing machine issue. I understand you're experiencing: "{query}"

**Next Steps:**
I'm processing your query and will provide detailed troubleshooting steps in the next version. For now, here are some general steps:

1. Check if the machine is plugged in and getting power
2. Ensure the door/lid is properly closed and latched
3. Verify water supply valves are turned on
4. Check for any error codes on the display

Is your issue related to any of these areas? Please let me know and I can provide more specific guidance."""
    
    async def _generate_clarification_response(self) -> str:
        """
        Generate response requesting clarification.
        
        Returns:
            Clarification request text
        """
        return """I'd be happy to help with your washing machine issue! 

Could you please provide more details about the problem you're experiencing? For example:
• What exactly is happening (or not happening)?
• Any error codes or unusual sounds?
• When did the problem start?

The more details you provide, the better I can assist you with troubleshooting! 🔧"""