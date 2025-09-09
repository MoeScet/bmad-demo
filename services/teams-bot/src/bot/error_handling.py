"""
Comprehensive Error Handling for Teams Bot Service
Centralized error handling, logging, and user-friendly error responses.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import structlog
from fastapi import HTTPException, status

from config.settings import teams_config

# Setup structured logging
logger = structlog.get_logger(__name__)


class TeamsErrorHandler:
    """
    Centralized error handling for Teams bot operations.
    
    Provides structured error logging, user-friendly error messages,
    and consistent error response formatting.
    """
    
    # User-friendly error messages without internal details
    USER_ERROR_MESSAGES = {
        "authentication_failed": "Authentication failed. Please try signing in again.",
        "bot_registration_error": "Bot registration issue. Please contact support.",
        "communication_failure": "Communication error. Please try again in a moment.",
        "service_unavailable": "Service temporarily unavailable. Please try again later.",
        "invalid_request": "Invalid request format. Please try again.",
        "processing_error": "Unable to process your request. Please try again.",
        "timeout_error": "Request timed out. Please try again.",
        "unknown_error": "An unexpected error occurred. Please try again later."
    }
    
    def __init__(self):
        """Initialize error handler."""
        self.correlation_id = str(uuid.uuid4())
        
        logger.info(
            "Teams error handler initialized",
            correlation_id=self.correlation_id,
            service="teams-bot"
        )
    
    def handle_bot_registration_error(
        self,
        error: Exception,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle bot registration errors with structured logging.
        
        Args:
            error: Original exception
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        logger.error(
            "Bot registration error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=self.USER_ERROR_MESSAGES["bot_registration_error"]
        )
    
    def handle_authentication_error(
        self,
        error: Exception,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle authentication failures with structured logging.
        
        Args:
            error: Original exception
            user_id: Teams user ID (if available)
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        logger.error(
            "Authentication error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            user_id=user_id or "unknown",
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.USER_ERROR_MESSAGES["authentication_failed"]
        )
    
    def handle_communication_failure(
        self,
        error: Exception,
        endpoint: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle communication failures with external services.
        
        Args:
            error: Original exception
            endpoint: Failed endpoint (if applicable)
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        logger.error(
            "Communication failure occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            endpoint=endpoint or "unknown",
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=self.USER_ERROR_MESSAGES["communication_failure"]
        )
    
    def handle_timeout_error(
        self,
        error: Exception,
        operation: Optional[str] = None,
        timeout_duration: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle timeout errors with circuit breaker pattern support.
        
        Args:
            error: Original exception
            operation: Operation that timed out
            timeout_duration: Timeout duration in seconds
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        logger.error(
            "Timeout error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            operation=operation or "unknown",
            timeout_duration=timeout_duration,
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=self.USER_ERROR_MESSAGES["timeout_error"]
        )
    
    def handle_processing_error(
        self,
        error: Exception,
        user_id: Optional[str] = None,
        message_content: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle message processing errors.
        
        Args:
            error: Original exception
            user_id: Teams user ID
            message_content: User message (will not be logged per security requirements)
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # CRITICAL: Never log sensitive data (user conversation content)
        logger.error(
            "Message processing error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            user_id=user_id or "unknown",
            message_length=len(message_content) if message_content else 0,
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=self.USER_ERROR_MESSAGES["processing_error"]
        )
    
    def handle_validation_error(
        self,
        error: Exception,
        request_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle request validation errors.
        
        Args:
            error: Original exception
            request_data: Request data (will be sanitized before logging)
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Sanitize request data for logging (remove sensitive fields)
        sanitized_data = {}
        if request_data:
            sanitized_data = {
                key: value if key not in ["text", "content", "message"] else f"<{len(str(value))} chars>"
                for key, value in request_data.items()
            }
        
        logger.error(
            "Request validation error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            sanitized_request=sanitized_data,
            error=str(error),
            error_type=type(error).__name__
        )
        
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.USER_ERROR_MESSAGES["invalid_request"]
        )
    
    def handle_unknown_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> HTTPException:
        """
        Handle unknown/unexpected errors with full context logging.
        
        Args:
            error: Original exception
            context: Additional context information
            correlation_id: Request correlation ID
            
        Returns:
            HTTPException with user-friendly message
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        logger.critical(
            "Unknown error occurred",
            correlation_id=correlation_id,
            service="teams-bot",
            context=context or {},
            error=str(error),
            error_type=type(error).__name__,
            environment=teams_config.ENVIRONMENT
        )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=self.USER_ERROR_MESSAGES["unknown_error"]
        )
    
    def create_error_response(
        self,
        error_type: str,
        correlation_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response format.
        
        Args:
            error_type: Type of error from USER_ERROR_MESSAGES
            correlation_id: Request correlation ID
            additional_context: Additional context (non-sensitive)
            
        Returns:
            Standardized error response dictionary
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        response = {
            "status": "error",
            "message": self.USER_ERROR_MESSAGES.get(error_type, self.USER_ERROR_MESSAGES["unknown_error"]),
            "correlation_id": correlation_id,
            "timestamp": "2025-09-08T00:00:00Z",  # Will be dynamic in production
            "service": "teams-bot",
            "version": teams_config.SERVICE_VERSION
        }
        
        if additional_context:
            response["context"] = additional_context
        
        return response


# Global error handler instance
teams_error_handler = TeamsErrorHandler()