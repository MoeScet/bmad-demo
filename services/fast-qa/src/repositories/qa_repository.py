"""
Repository pattern implementation for Q&A database operations.
"""
from __future__ import annotations

import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from models.qa_entry import QAEntry
from models.schemas import QAEntryCreate, QAEntryUpdate, QASearchRequest
from services.content_validator import content_validator

logger = structlog.get_logger(__name__)


class QARepository:
    """Repository for Q&A entry database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_entries(
        self, 
        search_request: QASearchRequest,
        correlation_id: Optional[str] = None
    ) -> Tuple[List[QAEntry], int, int]:
        """
        Search Q&A entries using full-text search and keyword matching.
        
        Args:
            search_request: Search parameters
            correlation_id: Request correlation ID for logging
            
        Returns:
            Tuple of (matching_entries, total_count, query_time_ms)
        """
        start_time = datetime.utcnow()
        
        try:
            # Base query for active entries
            query = select(QAEntry).where(QAEntry.is_active == True)
            count_query = select(func.count(QAEntry.id)).where(QAEntry.is_active == True)
            
            # Apply safety level filters
            if search_request.safety_levels:
                safety_filter = QAEntry.safety_level.in_(search_request.safety_levels)
                query = query.where(safety_filter)
                count_query = count_query.where(safety_filter)
            
            # Build search conditions
            search_conditions = []
            search_query = search_request.query.strip().lower()
            
            # Full-text search using TSVECTOR
            if len(search_query) >= 3:
                # Create search vector from query
                ts_query = func.plainto_tsquery('english', search_query)
                search_conditions.append(
                    QAEntry.search_vector.op('@@')(ts_query)
                )
                
                # Keyword array matching
                search_conditions.append(
                    func.array_to_string(QAEntry.keywords, ' ').ilike(f'%{search_query}%')
                )
                
                # Basic text matching as fallback
                search_conditions.append(
                    or_(
                        QAEntry.question.ilike(f'%{search_query}%'),
                        QAEntry.answer.ilike(f'%{search_query}%')
                    )
                )
            
            if search_conditions:
                combined_conditions = or_(*search_conditions)
                query = query.where(combined_conditions)
                count_query = count_query.where(combined_conditions)
            
            # Order by relevance (success rate, usage count, then creation date)
            query = query.order_by(
                desc(QAEntry.success_rate),
                desc(QAEntry.usage_count),
                desc(QAEntry.created_at)
            )
            
            # Apply limits
            query = query.limit(search_request.max_results or 10)
            
            # Execute queries
            result = await self.session.execute(query)
            entries = result.scalars().all()
            
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # Calculate query time
            end_time = datetime.utcnow()
            query_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(
                "Q&A search completed",
                correlation_id=correlation_id,
                service="fast-qa",
                query_time_ms=query_time_ms,
                results_count=len(entries),
                total_count=total_count
            )
            
            return list(entries), total_count, query_time_ms
            
        except Exception as e:
            logger.error(
                "Q&A search failed",
                correlation_id=correlation_id,
                service="fast-qa",
                error=str(e),
                query=search_request.query
            )
            raise

    async def get_entry_by_id(self, entry_id: uuid.UUID) -> Optional[QAEntry]:
        """Get Q&A entry by ID."""
        try:
            result = await self.session.execute(
                select(QAEntry).where(QAEntry.id == entry_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                "Failed to get Q&A entry by ID",
                service="fast-qa",
                entry_id=str(entry_id),
                error=str(e)
            )
            raise

    async def list_entries(
        self, 
        page: int = 1, 
        page_size: int = 20,
        active_only: bool = True
    ) -> Tuple[List[QAEntry], int]:
        """List Q&A entries with pagination."""
        try:
            offset = (page - 1) * page_size
            
            # Base query
            query = select(QAEntry)
            count_query = select(func.count(QAEntry.id))
            
            if active_only:
                query = query.where(QAEntry.is_active == True)
                count_query = count_query.where(QAEntry.is_active == True)
            
            # Apply pagination
            query = (
                query
                .order_by(desc(QAEntry.created_at))
                .offset(offset)
                .limit(page_size)
            )
            
            # Execute queries
            result = await self.session.execute(query)
            entries = result.scalars().all()
            
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            return list(entries), total_count
            
        except Exception as e:
            logger.error(
                "Failed to list Q&A entries",
                service="fast-qa",
                error=str(e),
                page=page,
                page_size=page_size
            )
            raise

    async def create_entry(self, entry_data: QAEntryCreate) -> QAEntry:
        """Create a new Q&A entry with content validation."""
        try:
            # Validate content before creation
            validation = content_validator.validate_content(
                entry_data.question,
                entry_data.answer,
                entry_data.keywords
            )
            
            if not validation.is_valid:
                raise ValueError(f"Content validation failed: {'; '.join(validation.issues)}")
            
            # Use validated safety level if different from provided
            safety_level = validation.suggested_safety_level if validation.confidence_score > 0.7 else entry_data.safety_level
            
            # Create entry instance
            entry = QAEntry(
                question=entry_data.question,
                answer=entry_data.answer,
                keywords=entry_data.keywords,
                supported_models=entry_data.supported_models,
                safety_level=safety_level,
                complexity_score=entry_data.complexity_score,
            )
            
            self.session.add(entry)
            await self.session.commit()
            await self.session.refresh(entry)
            
            # Update search vector
            await self._update_search_vector(entry.id)
            
            logger.info(
                "Created new Q&A entry",
                service="fast-qa",
                entry_id=str(entry.id),
                safety_level=entry.safety_level
            )
            
            return entry
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to create Q&A entry",
                service="fast-qa",
                error=str(e)
            )
            raise

    async def update_entry(self, entry_id: uuid.UUID, entry_data: QAEntryUpdate) -> Optional[QAEntry]:
        """Update an existing Q&A entry."""
        try:
            # Get existing entry
            entry = await self.get_entry_by_id(entry_id)
            if not entry:
                return None
            
            # Update fields
            update_data = entry_data.dict(exclude_unset=True)
            if update_data:
                for field, value in update_data.items():
                    setattr(entry, field, value)
                
                entry.updated_at = datetime.utcnow()
                await self.session.commit()
                
                # Update search vector if content changed
                if 'question' in update_data or 'answer' in update_data:
                    await self._update_search_vector(entry.id)
                
                logger.info(
                    "Updated Q&A entry",
                    service="fast-qa",
                    entry_id=str(entry_id),
                    updated_fields=list(update_data.keys())
                )
            
            return entry
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to update Q&A entry",
                service="fast-qa",
                entry_id=str(entry_id),
                error=str(e)
            )
            raise

    async def delete_entry(self, entry_id: uuid.UUID) -> bool:
        """Soft delete a Q&A entry by setting is_active to False."""
        try:
            result = await self.session.execute(
                update(QAEntry)
                .where(QAEntry.id == entry_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            if result.rowcount > 0:
                await self.session.commit()
                logger.info(
                    "Deleted Q&A entry",
                    service="fast-qa",
                    entry_id=str(entry_id)
                )
                return True
            
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to delete Q&A entry",
                service="fast-qa",
                entry_id=str(entry_id),
                error=str(e)
            )
            raise

    async def increment_usage_count(self, entry_id: uuid.UUID) -> None:
        """Increment usage count for a Q&A entry."""
        try:
            await self.session.execute(
                update(QAEntry)
                .where(QAEntry.id == entry_id)
                .values(
                    usage_count=QAEntry.usage_count + 1,
                    updated_at=datetime.utcnow()
                )
            )
            await self.session.commit()
            
        except Exception as e:
            logger.error(
                "Failed to increment usage count",
                service="fast-qa",
                entry_id=str(entry_id),
                error=str(e)
            )
            # Don't raise - usage tracking is not critical

    async def _update_search_vector(self, entry_id: uuid.UUID) -> None:
        """Update search vector for full-text search."""
        try:
            # Update TSVECTOR from question and answer content
            await self.session.execute(
                text("""
                    UPDATE qa_entries 
                    SET search_vector = to_tsvector('english', question || ' ' || answer)
                    WHERE id = :entry_id
                """),
                {"entry_id": entry_id}
            )
            await self.session.commit()
            
        except Exception as e:
            logger.error(
                "Failed to update search vector",
                service="fast-qa",
                entry_id=str(entry_id),
                error=str(e)
            )
            # Don't raise - search vector update is not critical for basic functionality