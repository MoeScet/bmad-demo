"""
Async database connection and session management.
"""
from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import structlog
from config.settings import fast_qa_config

logger = structlog.get_logger(__name__)

# Create async engine with conditional connect_args for SQLite vs PostgreSQL
connect_args = {}
if "sqlite" in fast_qa_config.FAST_QA_DATABASE_URL:
    # SQLite-specific settings
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL-specific settings
    connect_args = {
        "command_timeout": int(fast_qa_config.FAST_QA_TIMEOUT),
        "server_settings": {
            "application_name": f"fast-qa-{fast_qa_config.SERVICE_VERSION}",
        },
    }

engine = create_async_engine(
    fast_qa_config.FAST_QA_DATABASE_URL,
    echo=fast_qa_config.is_development(),
    poolclass=NullPool,  # Use NullPool for better resource management
    connect_args=connect_args,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database sessions.
    
    Yields:
        AsyncSession: Database session for dependency injection
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(
                "Database session error",
                service="fast-qa",
                error=str(e)
            )
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """
    Check database connectivity for health checks.
    
    Returns:
        bool: True if connection is successful
    """
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(
            "Database connectivity check failed",
            service="fast-qa",
            error=str(e)
        )
        return False