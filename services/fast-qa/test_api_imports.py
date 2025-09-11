#!/usr/bin/env python3
"""Test API module imports to find the hanging import."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing API imports...")

try:
    from config.settings import fast_qa_config
    print("✓ Config imported")
except Exception as e:
    print(f"✗ Config failed: {e}")

try:
    from api.health import router as health_router
    print("✓ Health router imported")
except Exception as e:
    print(f"✗ Health router failed: {e}")

try:
    from api.qa_search import router as search_router
    print("✓ Search router imported")
except Exception as e:
    print(f"✗ Search router failed: {e}")

try:
    from api.qa_management import router as management_router
    print("✓ Management router imported")
except Exception as e:
    print(f"✗ Management router failed: {e}")

print("All API imports tested!")