"""
Initialize SQLite database for Fast Q&A Service testing.
"""
import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.database import engine
from models.qa_entry import Base

async def init_database():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("SQLite database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())