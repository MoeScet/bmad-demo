"""
Semantic Search Service

FastAPI service that provides semantic search capabilities using ChromaDB
for vector similarity search with sentence-transformers embeddings.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from .api import router as api_router
from .config.settings import get_settings
from shared.python.utils.health import create_health_service
from shared.python.database import get_vector_client
from shared.python.utils.logging import setup_logging


# Global health service
health_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    global health_service

    settings = get_settings()

    # Setup logging
    setup_logging(
        service_name=settings.SERVICE_NAME,
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Semantic Search Service", extra={"version": settings.SERVICE_VERSION})

    # Initialize health service with ChromaDB dependency
    health_service = create_health_service(
        service_name=settings.SERVICE_NAME,
        include_chromadb=True
    )

    # Test ChromaDB connection on startup
    try:
        async with get_vector_client(settings.CHROMA_HOST, settings.CHROMA_PORT) as client:
            await client.health_check()
            logger.info("ChromaDB connection verified successfully")
    except Exception as e:
        logger.error("ChromaDB connection failed on startup", extra={"error": str(e)})
        # Don't fail startup - service should handle ChromaDB unavailability gracefully

    yield

    logger.info("Shutting down Semantic Search Service")


# Create FastAPI app
app = FastAPI(
    title="BMAD Semantic Search Service",
    description="Vector-based semantic search using ChromaDB and sentence-transformers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(request: Request):
    """Service health check endpoint"""
    correlation_id = request.headers.get("X-Correlation-ID")
    return await health_service.health_check(correlation_id)


@app.get("/health/ready")
async def readiness_check(request: Request):
    """Service readiness check endpoint"""
    correlation_id = request.headers.get("X-Correlation-ID")
    return await health_service.readiness_check(correlation_id)


@app.get("/health/live")
async def liveness_check(request: Request):
    """Service liveness check endpoint"""
    correlation_id = request.headers.get("X-Correlation-ID")
    return await health_service.liveness_check(correlation_id)


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )