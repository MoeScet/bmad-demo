"""
Fast Q&A search API endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config.settings import fast_qa_config
from models.database import get_database_session
from models.schemas import (
    QASearchRequest, QASearchResponse, QASearchResult, 
    QAEntryResponse, APIResponse
)
from repositories.qa_repository import QARepository

router = APIRouter()
logger = structlog.get_logger(__name__)


def calculate_relevance_score(entry, search_query: str, match_type: str) -> float:
    """Calculate relevance score for search results."""
    base_score = 0.5
    
    # Boost based on success rate
    success_boost = entry.success_rate * 0.3
    
    # Boost based on usage count (normalized)
    usage_boost = min(entry.usage_count / 100.0, 0.2)
    
    # Match type specific scoring
    match_boosts = {
        'exact_keyword': 0.4,
        'full_text': 0.3,
        'partial_text': 0.2,
        'fallback': 0.1
    }
    
    match_boost = match_boosts.get(match_type, 0.1)
    
    # Calculate final score
    final_score = min(base_score + success_boost + usage_boost + match_boost, 1.0)
    return round(final_score, 3)


async def get_qa_repository(
    session: AsyncSession = Depends(get_database_session)
) -> QARepository:
    """Dependency to get QA repository instance."""
    return QARepository(session)


@router.post("/search", response_model=APIResponse)
async def search_qa_entries(
    search_request: QASearchRequest,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Search Q&A entries using keyword matching and full-text search.
    
    Provides sub-5 second response times with relevance ranking.
    """
    try:
        # Generate correlation ID if not provided
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A search request received",
            correlation_id=correlation_id,
            service="fast-qa",
            query=search_request.query,
            max_results=search_request.max_results
        )
        
        # Apply timeout constraint
        import asyncio
        search_task = qa_repo.search_entries(search_request, correlation_id)
        
        try:
            entries, total_count, query_time_ms = await asyncio.wait_for(
                search_task, 
                timeout=fast_qa_config.FAST_QA_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Q&A search timeout",
                correlation_id=correlation_id,
                service="fast-qa",
                timeout_seconds=fast_qa_config.FAST_QA_TIMEOUT
            )
            return {
                "data": None,
                "error": {
                    "message": "Search timeout",
                    "code": "SEARCH_TIMEOUT",
                    "timeout_seconds": fast_qa_config.FAST_QA_TIMEOUT
                }
            }
        
        # Build search results with relevance scoring
        results = []
        for entry in entries:
            # Determine match type (simplified for now)
            match_type = "full_text"
            
            # Calculate relevance score
            relevance_score = calculate_relevance_score(
                entry, search_request.query, match_type
            )
            
            # Apply minimum score threshold
            if relevance_score >= (search_request.min_score or fast_qa_config.FAST_QA_MIN_SCORE):
                search_result = QASearchResult(
                    entry=QAEntryResponse.from_orm(entry),
                    relevance_score=relevance_score,
                    match_type=match_type
                )
                results.append(search_result)
                
                # Increment usage count asynchronously (fire-and-forget)
                asyncio.create_task(qa_repo.increment_usage_count(entry.id))
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Build response
        search_response = QASearchResponse(
            results=results,
            total_count=len(results),
            query_time_ms=query_time_ms,
            applied_filters={
                "safety_levels": search_request.safety_levels,
                "min_score": search_request.min_score or fast_qa_config.FAST_QA_MIN_SCORE,
                "max_results": search_request.max_results
            }
        )
        
        logger.info(
            "Q&A search completed successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            results_returned=len(results),
            query_time_ms=query_time_ms
        )
        
        return {
            "data": search_response.dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Q&A search failed",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e),
            query=search_request.query
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Search operation failed",
                "code": "SEARCH_ERROR"
            }
        )


@router.get("/entry/{entry_id}", response_model=APIResponse)
async def get_qa_entry(
    entry_id: str,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """Get a specific Q&A entry by ID."""
    try:
        entry = await qa_repo.get_entry_by_id(entry_id)
        
        if not entry:
            return {
                "data": None,
                "error": {
                    "message": "Q&A entry not found",
                    "code": "ENTRY_NOT_FOUND",
                    "entry_id": str(entry_id)
                }
            }
        
        # Increment usage count
        asyncio.create_task(qa_repo.increment_usage_count(entry.id))
        
        return {
            "data": QAEntryResponse.from_orm(entry).dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to get Q&A entry",
            correlation_id=x_correlation_id,
            service="fast-qa",
            entry_id=str(entry_id),
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve Q&A entry",
                "code": "GET_ENTRY_ERROR"
            }
        )