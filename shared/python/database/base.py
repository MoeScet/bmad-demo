"""
SQLAlchemy database base and session management
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Base class for all models
Base = declarative_base()


class DatabaseBase(DeclarativeBase):
    """Modern SQLAlchemy 2.0 base class"""
    pass


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://bmad_user:bmad_password@localhost:5432/bmad_dev"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("DB_ECHO", False)),
    pool_pre_ping=True
)

# Create session factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)