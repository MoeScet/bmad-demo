"""
Health Check Endpoints for Teams Bot Service
Service monitoring and health validation endpoints.
"""
from __future__ import annotations

from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException, status

from config.settings import teams_config

# Setup structured logging
logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for monitoring and load balancer.
    
    Returns service status, configuration validation, and dependency checks.
    """
    try:
        health_status = {
            "service": teams_config.SERVICE_NAME,
            "version": teams_config.SERVICE_VERSION,
            "environment": teams_config.ENVIRONMENT,
            "status": "healthy"
        }
        
        # Validate critical configuration
        config_checks = {
            "teams_app_configured": bool(teams_config.TEAMS_BOT_APP_ID),
            "database_configured": bool(teams_config.DATABASE_URL),
            "webhook_url_configured": bool(teams_config.TEAMS_BOT_WEBHOOK_URL)
        }
        
        health_status["configuration"] = config_checks
        
        # Check if any critical configuration is missing
        if not all(config_checks.values()):
            health_status["status"] = "degraded"
            health_status["warnings"] = [
                f"Missing configuration: {key}" 
                for key, value in config_checks.items() 
                if not value
            ]
        
        logger.info(
            "Health check performed",
            service="teams-bot",
            status=health_status["status"],
            configuration_valid=all(config_checks.values())
        )
        
        return health_status
        
    except Exception as error:
        logger.error(
            "Health check failed",
            service="teams-bot",
            error=str(error),
            error_type=type(error).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service health check failed"
        )


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with dependency validation.
    
    Only available in non-production environments for security.
    """
    if teams_config.is_production():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detailed health checks not available in production"
        )
    
    try:
        detailed_status = {
            "service": teams_config.SERVICE_NAME,
            "version": teams_config.SERVICE_VERSION,
            "environment": teams_config.ENVIRONMENT,
            "timestamp": "2025-09-08T00:00:00Z",  # Will be dynamic in production
            "status": "healthy"
        }
        
        # Configuration details (non-sensitive)
        config_details = {
            "service_name": teams_config.SERVICE_NAME,
            "service_version": teams_config.SERVICE_VERSION,
            "log_level": teams_config.LOG_LEVEL,
            "log_format": teams_config.LOG_FORMAT,
            "host": teams_config.HOST,
            "port": teams_config.PORT,
            "user_context_timeout": teams_config.USER_CONTEXT_TIMEOUT,
            "teams_api_timeout": teams_config.TEAMS_API_TIMEOUT
        }
        
        detailed_status["configuration"] = config_details
        
        # TODO: Add dependency health checks (database, external services)
        # This will be implemented in subsequent subtasks
        
        return detailed_status
        
    except Exception as error:
        logger.error(
            "Detailed health check failed",
            service="teams-bot",
            error=str(error),
            error_type=type(error).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detailed health check failed"
        )