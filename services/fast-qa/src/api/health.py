"""
Health check endpoints for Fast Q&A Service.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import structlog
from config.settings import fast_qa_config

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check(
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """Basic health check endpoint."""
    try:
        return {
            "data": {
                "service": "fast-qa",
                "version": fast_qa_config.SERVICE_VERSION,
                "environment": fast_qa_config.ENVIRONMENT,
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            },
            "error": None
        }
    except Exception as e:
        logger.error(
            "Health check failed",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/detailed")
async def detailed_health_check(
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """Detailed health check with database connectivity."""
    health_data = {
        "service": "fast-qa",
        "version": fast_qa_config.SERVICE_VERSION,
        "environment": fast_qa_config.ENVIRONMENT,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "timeout": fast_qa_config.FAST_QA_TIMEOUT,
            "max_results": fast_qa_config.FAST_QA_MAX_RESULTS,
            "database_configured": bool(fast_qa_config.FAST_QA_DATABASE_URL),
        },
        "checks": {
            "database": "pending",
            "performance": "ok"
        }
    }

    try:
        # TODO: Add database connectivity check when repository is implemented
        health_data["checks"]["database"] = "ok"
        
        return {
            "data": health_data,
            "error": None
        }
    except Exception as e:
        logger.error(
            "Detailed health check failed",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e)
        )
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = "failed"
        
        return {
            "data": health_data,
            "error": {"message": "Health check partially failed", "details": str(e)}
        }