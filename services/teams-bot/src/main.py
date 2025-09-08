"""
Microsoft Teams Bot Service - Main Application Entry Point
Provides Teams integration with query orchestration and health monitoring.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parents[3] / "shared" / "python"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config.base import TeamsConfig, load_config
from utils.logging import configure_logging, CorrelationMiddleware

# Load configuration
config = load_config(TeamsConfig)

# Configure logging
logger = configure_logging(
    service_name=config.SERVICE_NAME,
    service_version=config.SERVICE_VERSION,
    log_level=config.LOG_LEVEL,
    log_format=config.LOG_FORMAT,
    environment=config.ENVIRONMENT
)

# Create FastAPI application
app = FastAPI(
    title="BMAD Teams Bot Service",
    description="Microsoft Teams integration for washing machine troubleshooting assistance",
    version=config.SERVICE_VERSION,
    docs_url="/docs" if not config.is_production() else None,
    redoc_url="/redoc" if not config.is_production() else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationMiddleware)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancer."""
    return {
        "service": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "status": "healthy",
        "environment": config.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "BMAD Teams Bot Service",
        "version": config.SERVICE_VERSION,
        "environment": config.ENVIRONMENT,
        "docs": "/docs" if not config.is_production() else "disabled"
    }


# Teams Bot webhook endpoints will be added here
@app.post("/api/messages")
async def teams_webhook(request: Request):
    """Handle incoming Teams messages."""
    logger.info("Teams message received")
    # Teams bot implementation will be added in next story
    return {"status": "received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not config.is_production(),
        log_config=None  # Use our custom logging
    )