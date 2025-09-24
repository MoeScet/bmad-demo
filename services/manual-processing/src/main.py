"""
Manual Processing Service

FastAPI service for processing PDF manuals and creating vector embeddings
for the BMAD troubleshooting system.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api.upload import router as upload_router
from .api.processing import router as processing_router
from .api.health import router as health_router
from .config.settings import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Manual Processing Service")
    settings = get_settings()
    logger.info(f"Service configured for environment: {settings.ENVIRONMENT}")

    yield

    # Shutdown
    logger.info("Shutting down Manual Processing Service")


app = FastAPI(
    title="BMAD Manual Processing Service",
    description="PDF manual processing and vector embedding generation service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler with correlation ID support"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={'correlation_id': correlation_id}
    )

    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {
                "message": "Internal server error occurred during manual processing",
                "correlation_id": correlation_id
            }
        }
    )


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to all requests"""
    import uuid

    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation_id

    return response


# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(upload_router, prefix="/api/v1", tags=["upload"])
app.include_router(processing_router, prefix="/api/v1", tags=["processing"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "data": {
            "service": "BMAD Manual Processing Service",
            "status": "running",
            "version": "1.0.0",
            "description": "PDF manual processing and vector embedding generation"
        },
        "error": None
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )