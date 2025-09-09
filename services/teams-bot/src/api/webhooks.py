"""
Microsoft Teams Webhook Handlers
Teams message processing and Bot Framework integration endpoints.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException, Request, Response, status

from bot.adapters.teams_adapter import TeamsAdapter
from bot.teams_bot import TeamsBot
from config.settings import teams_config

# Setup structured logging
logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["webhooks"])

# Initialize Teams adapter and bot
teams_adapter = TeamsAdapter()
teams_bot = TeamsBot(
    conversation_state_accessor=teams_adapter.get_conversation_state_accessor("conversation_data"),
    user_state_accessor=teams_adapter.get_user_state_accessor("user_profile")
)


async def bot_logic(turn_context) -> None:
    """Bot logic handler for Teams adapter."""
    await teams_bot.on_turn(turn_context)
    await teams_adapter.save_conversation_state(turn_context)


@router.post("/messages")
async def handle_teams_message(request: Request) -> str:
    """
    Handle incoming Microsoft Teams messages through Bot Framework adapter.
    
    This endpoint receives webhook calls from Microsoft Teams Bot Framework
    and processes them through the Teams adapter and bot logic.
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Get authorization header for Bot Framework authentication
        auth_header = request.headers.get("Authorization", "")
        
        # Parse activity data from request
        activity_data = await request.json()
        
        logger.info(
            "Teams message received",
            correlation_id=correlation_id,
            service="teams-bot",
            activity_type=activity_data.get("type", "unknown"),
            conversation_id=activity_data.get("conversation", {}).get("id"),
            from_user_id=activity_data.get("from", {}).get("id")
        )
        
        # Process through Bot Framework adapter
        response_body = await teams_adapter.process_activity(
            auth_header=auth_header,
            activity_data=activity_data,
            bot_handler=bot_logic
        )
        
        logger.info(
            "Teams message processed successfully",
            correlation_id=correlation_id,
            service="teams-bot"
        )
        
        return response_body
        
    except Exception as error:
        logger.error(
            "Teams message processing failed",
            correlation_id=correlation_id,
            service="teams-bot",
            error=str(error),
            error_type=type(error).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message processing failed"
        )




@router.get("/health")
async def webhook_health() -> Dict[str, Any]:
    """Health check specifically for webhook endpoints."""
    return {
        "service": "teams-bot-webhooks",
        "status": "healthy",
        "endpoints": ["/api/messages"],
        "version": teams_config.SERVICE_VERSION
    }