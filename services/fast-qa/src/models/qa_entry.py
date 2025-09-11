"""
SQLAlchemy models for Q&A entries with full-text search support.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean, DECIMAL, Integer, String, Text, TIMESTAMP, 
    CheckConstraint, Index, text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# Import database-specific types conditionally
try:
    from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, ARRAY
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

Base = declarative_base()


class QAEntry(Base):
    """Q&A Entry model with full-text search and metadata."""
    
    __tablename__ = "qa_entries"

    # Primary key - use String for SQLite compatibility
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Core content
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Search optimization - use JSON for SQLite compatibility
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    search_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata - use JSON for SQLite compatibility
    supported_models: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    safety_level: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="safe",
        server_default="'safe'"
    )
    complexity_score: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=5,
        server_default="5"
    )

    # Usage tracking
    success_rate: Mapped[float] = mapped_column(
        DECIMAL(3, 2), 
        nullable=False, 
        default=0.0,
        server_default="0.0"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        server_default="0"
    )

    # Status and timestamps
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "safety_level IN ('safe', 'caution', 'professional')",
            name="check_safety_level"
        ),
        CheckConstraint(
            "complexity_score BETWEEN 1 AND 10",
            name="check_complexity_score"
        ),
        # Indexes for performance (SQLite compatible)
        Index("idx_qa_entries_safety_level", "safety_level"),
        Index("idx_qa_entries_is_active", "is_active"),
        Index("idx_qa_entries_success_rate", "success_rate"),
    )