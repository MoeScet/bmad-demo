"""
Centralized logging configuration for BMAD services.
Implements structured logging with correlation ID tracking and JSON formatting.
"""
from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.typing import FilteringBoundLogger, Processor

# Context variable for correlation ID tracking across async operations
correlation_id_context: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def add_correlation_id(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add correlation ID to log events for request tracing.
    
    Args:
        logger: The logger instance
        method_name: The log method name 
        event_dict: The event dictionary
        
    Returns:
        Updated event dictionary with correlation ID
    """
    correlation_id = correlation_id_context.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_service_context(service_name: str, service_version: str) -> Processor:
    """
    Create a processor to add service context to all log events.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        
    Returns:
        Processor function that adds service context
    """
    def processor(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        event_dict.update({
            "service": service_name,
            "version": service_version,
        })
        return event_dict
    
    return processor


def configure_logging(
    service_name: str,
    service_version: str,
    log_level: str = "INFO",
    log_format: str = "json",
    environment: str = "development"
) -> FilteringBoundLogger:
    """
    Configure structured logging for a BMAD service.
    
    Args:
        service_name: Name of the service (e.g., "teams-bot")
        service_version: Version of the service (e.g., "1.0.0")
        log_level: Logging level (DEBUG, INFO, WARN, ERROR, CRITICAL)
        log_format: Output format ("json" or "text")
        environment: Environment name (development, staging, production)
        
    Returns:
        Configured structured logger instance
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Common processors for all environments
    common_processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_service_context(service_name, service_version),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    
    # Environment-specific processors
    if environment == "development" or log_format == "text":
        processors = common_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        processors = common_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create and return logger instance
    logger = structlog.get_logger(service_name)
    
    # Log configuration details
    logger.info(
        "Logging configured",
        log_level=log_level,
        log_format=log_format,
        environment=environment,
    )
    
    return logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.
    
    Args:
        correlation_id: Correlation ID to set, generates new UUID if None
        
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_context.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.
    
    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id_context.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_context.set(None)


class CorrelationMiddleware:
    """
    FastAPI middleware for correlation ID handling.
    Extracts correlation ID from headers or generates new one.
    """
    
    def __init__(self, app, correlation_header: str = "X-Correlation-ID"):
        self.app = app
        self.correlation_header = correlation_header
    
    async def __call__(self, scope, receive, send):
        """Handle ASGI request with correlation ID management."""
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            correlation_id = headers.get(
                self.correlation_header.lower().encode(), 
                str(uuid.uuid4()).encode()
            ).decode()
            
            set_correlation_id(correlation_id)
            
            # Add correlation ID to response headers
            async def send_with_correlation(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    headers[self.correlation_header.encode()] = correlation_id.encode()
                    message["headers"] = list(headers.items())
                await send(message)
            
            await self.app(scope, receive, send_with_correlation)
        else:
            await self.app(scope, receive, send)


# Pre-configured logger instances for different log levels
def get_logger(service_name: str) -> FilteringBoundLogger:
    """Get a logger instance for the specified service."""
    return structlog.get_logger(service_name)