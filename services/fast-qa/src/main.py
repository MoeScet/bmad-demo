"""
Fast Q&A Service - Main Application Entry Point
Provides sub-5 second lookup of curated troubleshooting solutions.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add current directory to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
from config.settings import fast_qa_config
from api.health import router as health_router
from api.qa_search import router as search_router
from api.qa_management import router as management_router

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
    title="Fast Q&A Service",
    description="Sub-5 second lookup of curated washing machine troubleshooting solutions",
    version=fast_qa_config.SERVICE_VERSION,
    docs_url="/docs" if not fast_qa_config.is_production() else None,
    redoc_url="/redoc" if not fast_qa_config.is_production() else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=fast_qa_config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(search_router, prefix="/qa")
app.include_router(management_router, prefix="/qa")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "data": {
            "service": "Fast Q&A Service",
            "version": fast_qa_config.SERVICE_VERSION,
            "environment": fast_qa_config.ENVIRONMENT,
            "docs": "/docs" if not fast_qa_config.is_production() else "disabled"
        },
        "error": None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=fast_qa_config.HOST,
        port=fast_qa_config.PORT,
        reload=not fast_qa_config.is_production(),
        log_config=None  # Use our custom logging
    )