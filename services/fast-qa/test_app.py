#!/usr/bin/env python3
"""Test FastAPI app creation without running uvicorn."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Creating FastAPI app...")

try:
    from fastapi import FastAPI
    from config.settings import fast_qa_config
    from api.health import router as health_router
    from api.qa_search import router as search_router
    from api.qa_management import router as management_router
    
    # Create the app (same as main.py but without uvicorn.run)
    app = FastAPI(
        title="Fast Q&A Service",
        description="Sub-5 second lookup of curated washing machine troubleshooting solutions",
        version=fast_qa_config.SERVICE_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(search_router, prefix="/qa")
    app.include_router(management_router, prefix="/qa")
    
    print("✓ FastAPI app created successfully!")
    print(f"✓ Config loaded - Port: {fast_qa_config.PORT}")
    print("App routes:")
    for route in app.routes:
        print(f"  - {route.path}")
    
except Exception as e:
    print(f"✗ App creation failed: {e}")
    import traceback
    traceback.print_exc()