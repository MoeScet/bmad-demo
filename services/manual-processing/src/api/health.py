"""
Health check endpoints for Manual Processing Service
"""

import time
import logging
from typing import Dict, Any

import httpx
from fastapi import APIRouter, Request
from sqlalchemy import text

from ..config.settings import get_settings
from shared.python.database.connection import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Comprehensive health check for manual processing service
    """
    start_time = time.time()
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    settings = get_settings()

    health_status = {
        "service": "manual-processing",
        "status": "healthy",
        "checks": {},
        "response_time_ms": 0.0
    }

    # Check database connectivity
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(
            f"Database health check failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check ChromaDB connectivity
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.CHROMADB_BASE_URL}/heartbeat")
            if response.status_code == 200:
                health_status["checks"]["chromadb"] = "healthy"
            else:
                health_status["checks"]["chromadb"] = "unhealthy"
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(
            f"ChromaDB health check failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        health_status["checks"]["chromadb"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check upload directory accessibility
    try:
        import os
        os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
        health_status["checks"]["upload_directory"] = "healthy"
    except Exception as e:
        logger.error(
            f"Upload directory check failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        health_status["checks"]["upload_directory"] = "unhealthy"
        health_status["status"] = "degraded"

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return {
        "data": health_status,
        "error": None
    }


@router.get("/ready")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        # Quick database check
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))

        return {
            "data": {
                "service": "manual-processing",
                "status": "ready"
            },
            "error": None
        }
    except Exception as e:
        logger.error(
            f"Readiness check failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        return {
            "data": None,
            "error": {
                "message": "Service not ready",
                "correlation_id": correlation_id
            }
        }