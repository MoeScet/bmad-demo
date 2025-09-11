"""
Test configuration and fixtures for Fast Q&A Service.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

# Set test environment before imports
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

os.environ["ENVIRONMENT"] = "test"
os.environ["FAST_QA_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from main import app
from models.database import get_database_session
from models.qa_entry import Base, QAEntry


# Test database setup
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

test_async_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with test_async_session_factory() as session:
        yield session


async def setup_test_database():
    """Set up test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def client() -> TestClient:
    """Create a test client with database dependency override."""
    
    # Set up database tables
    asyncio.run(setup_test_database())
    
    async def override_get_database_session():
        async with test_async_session_factory() as session:
            yield session
    
    app.dependency_overrides[get_database_session] = override_get_database_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_qa_entry(db_session: AsyncSession) -> QAEntry:
    """Create a sample Q&A entry for testing."""
    entry = QAEntry(
        question="Why won't my washing machine start?",
        answer="Check if the machine is plugged in, the door is properly closed, and water supply is turned on.",
        keywords=["won't start", "power", "door", "water supply"],
        supported_models=["LG WM3900", "Samsung WF45"],
        safety_level="safe",
        complexity_score=2
    )
    
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    
    return entry


@pytest.fixture
async def multiple_qa_entries(db_session: AsyncSession) -> list[QAEntry]:
    """Create multiple Q&A entries for testing."""
    entries = [
        QAEntry(
            question="Why won't my washing machine start?",
            answer="Check if the machine is plugged in, the door is properly closed.",
            keywords=["won't start", "power", "door"],
            supported_models=["LG WM3900"],
            safety_level="safe",
            complexity_score=2
        ),
        QAEntry(
            question="My washing machine is making loud noises",
            answer="This usually indicates an unbalanced load. Stop the machine and redistribute clothes.",
            keywords=["loud noise", "spin cycle", "unbalanced"],
            supported_models=["Samsung WF45"],
            safety_level="safe",
            complexity_score=3
        ),
        QAEntry(
            question="Water is not draining from my washing machine",
            answer="Check if the drain hose is kinked or clogged. Clean the lint filter.",
            keywords=["not draining", "drain hose", "lint filter"],
            supported_models=["Whirlpool WTW"],
            safety_level="caution",
            complexity_score=4
        ),
        QAEntry(
            question="Motor coupling replacement procedure",
            answer="This requires electrical testing and component replacement by a qualified technician.",
            keywords=["motor coupling", "electrical", "technician"],
            supported_models=["GE GTW"],
            safety_level="professional",
            complexity_score=9
        )
    ]
    
    for entry in entries:
        db_session.add(entry)
    
    await db_session.commit()
    
    # Refresh all entries
    for entry in entries:
        await db_session.refresh(entry)
    
    return entries