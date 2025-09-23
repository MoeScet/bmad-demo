"""
Health check utilities for BMAD services.

Provides standardized health check endpoints with dependency validation.
Follows coding standards for response format and correlation ID propagation.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
import uuid

from ..database.vector_client import get_vector_client, VectorDatabaseError


class HealthCheckService:
    """
    Standardized health check service for BMAD applications.

    Provides health endpoints with dependency checking following
    coding standards for response format and monitoring integration.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = time.time()
        self._dependency_checks: List[Callable[[], Awaitable[Dict[str, Any]]]] = []

    def add_dependency_check(self, check_func: Callable[[], Awaitable[Dict[str, Any]]]):
        """Add a dependency health check function"""
        self._dependency_checks.append(check_func)

    async def health_check(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive health check

        Returns:
            Standardized health response format:
            {data: {...}, error: null} or {data: null, error: {...}}
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            uptime = time.time() - self.start_time

            # Basic service health
            health_data = {
                "service": self.service_name,
                "status": "healthy",
                "uptime_seconds": round(uptime, 2),
                "timestamp": time.time(),
                "correlation_id": correlation_id,
                "dependencies": {}
            }

            # Check all dependencies
            for check_func in self._dependency_checks:
                try:
                    dep_result = await asyncio.wait_for(check_func(), timeout=5.0)
                    dep_name = dep_result.get("name", "unknown")
                    health_data["dependencies"][dep_name] = {
                        "status": dep_result.get("status", "unknown"),
                        "details": dep_result.get("details", {})
                    }
                except asyncio.TimeoutError:
                    health_data["dependencies"]["timeout_dependency"] = {
                        "status": "unhealthy",
                        "details": {"error": "health check timeout"}
                    }
                except Exception as e:
                    health_data["dependencies"]["failed_dependency"] = {
                        "status": "unhealthy",
                        "details": {"error": str(e)}
                    }

            # Determine overall status
            unhealthy_deps = [
                name for name, dep in health_data["dependencies"].items()
                if dep["status"] != "healthy"
            ]

            if unhealthy_deps:
                health_data["status"] = "degraded"
                health_data["unhealthy_dependencies"] = unhealthy_deps

            return {"data": health_data, "error": None}

        except Exception as e:
            return {
                "data": None,
                "error": {
                    "message": "Health check failed",
                    "details": str(e),
                    "correlation_id": correlation_id
                }
            }

    async def readiness_check(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if service is ready to accept traffic

        Returns:
            Readiness status in standard format
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            # For readiness, all dependencies must be healthy
            health_result = await self.health_check(correlation_id)

            if health_result["error"]:
                return {
                    "data": None,
                    "error": {
                        "message": "Service not ready",
                        "details": "Health check failed",
                        "correlation_id": correlation_id
                    }
                }

            health_data = health_result["data"]
            is_ready = health_data["status"] in ["healthy"]

            return {
                "data": {
                    "service": self.service_name,
                    "ready": is_ready,
                    "timestamp": time.time(),
                    "correlation_id": correlation_id
                },
                "error": None
            }

        except Exception as e:
            return {
                "data": None,
                "error": {
                    "message": "Readiness check failed",
                    "details": str(e),
                    "correlation_id": correlation_id
                }
            }

    async def liveness_check(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Simple liveness check - just verify service is running

        Returns:
            Liveness status in standard format
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        return {
            "data": {
                "service": self.service_name,
                "alive": True,
                "timestamp": time.time(),
                "correlation_id": correlation_id
            },
            "error": None
        }


async def chromadb_health_check(
    host: Optional[str] = None,
    port: Optional[int] = None
) -> Dict[str, Any]:
    """
    ChromaDB-specific health check function

    Returns:
        Health check result with ChromaDB connection status
    """
    try:
        async with get_vector_client(host=host, port=port) as client:
            health_result = await client.health_check()

            return {
                "name": "chromadb",
                "status": health_result["status"],
                "details": {
                    "host": health_result["host"],
                    "port": health_result["port"],
                    "correlation_id": health_result["correlation_id"]
                }
            }

    except VectorDatabaseError as e:
        return {
            "name": "chromadb",
            "status": "unhealthy",
            "details": {"error": str(e)}
        }
    except Exception as e:
        return {
            "name": "chromadb",
            "status": "unhealthy",
            "details": {"error": f"Unexpected error: {str(e)}"}
        }


def create_health_service(service_name: str, include_chromadb: bool = False) -> HealthCheckService:
    """
    Factory function to create health service with common dependencies

    Args:
        service_name: Name of the service
        include_chromadb: Whether to include ChromaDB health check

    Returns:
        Configured HealthCheckService instance
    """
    health_service = HealthCheckService(service_name)

    if include_chromadb:
        health_service.add_dependency_check(chromadb_health_check)

    return health_service