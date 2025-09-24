"""
SQLAlchemy model for manual content table
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.sql import func
import uuid

from ..database.base import Base


class ManualContent(Base):
    """Manual content model matching the database schema"""

    __tablename__ = "manual_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer = Column(String(100), nullable=False)
    model_series = Column(String(100), nullable=False)
    section_title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(
        String(50),
        CheckConstraint(
            "content_type IN ('troubleshooting', 'maintenance', 'safety', 'warranty')"
        ),
        nullable=True
    )
    search_vector = Column(TSVECTOR)
    confidence_score = Column(Numeric(3, 2), default=0.0)
    source_manual = Column(String(255))
    page_reference = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ManualContent(id={self.id}, manufacturer={self.manufacturer}, section_title={self.section_title})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'manufacturer': self.manufacturer,
            'model_series': self.model_series,
            'section_title': self.section_title,
            'content': self.content,
            'content_type': self.content_type,
            'confidence_score': float(self.confidence_score) if self.confidence_score else 0.0,
            'source_manual': self.source_manual,
            'page_reference': self.page_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }