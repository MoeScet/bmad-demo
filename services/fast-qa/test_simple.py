#!/usr/bin/env python3
"""Simple test to check if basic imports work."""

print("Testing basic imports...")

try:
    import fastapi
    print("✓ FastAPI imported successfully")
except Exception as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    from pydantic_settings import BaseSettings
    print("✓ Pydantic settings imported successfully")
except Exception as e:
    print(f"✗ Pydantic settings import failed: {e}")

try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from config.settings import fast_qa_config
    print(f"✓ Config loaded successfully - Port: {fast_qa_config.PORT}")
except Exception as e:
    print(f"✗ Config import failed: {e}")

print("Test complete!")