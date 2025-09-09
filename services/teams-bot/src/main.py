"""
Microsoft Teams Bot Service - Main Application Entry Point
Provides Teams integration with query orchestration and health monitoring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Add shared modules to path
#sys.path.insert(0, str(Path(__file__).parents[3] / "shared" / "python"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import structlog
from config.settings import teams_config
from api.webhooks import router as webhooks_router
from api.health import router as health_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="BMAD Teams Bot Service",
    description="Microsoft Teams integration for washing machine troubleshooting assistance",
    version=teams_config.SERVICE_VERSION,
    docs_url="/docs" if not teams_config.is_production() else None,
    redoc_url="/redoc" if not teams_config.is_production() else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=teams_config.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(webhooks_router)
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "BMAD Teams Bot Service",
        "version": teams_config.SERVICE_VERSION,
        "environment": teams_config.ENVIRONMENT,
        "docs": "/docs" if not teams_config.is_production() else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=teams_config.HOST,
        port=teams_config.PORT,
        reload=not teams_config.is_production(),
        log_config=None  # Use our custom logging
    )