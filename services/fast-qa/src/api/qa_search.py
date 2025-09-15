"""
Fast Q&A search API endpoints.
"""
from __future__ import annotations

import asyncio
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
    QAEntryResponse, APIResponse, QAFeedbackRequest
)
from repositories.qa_repository import QARepository

router = APIRouter()
logger = structlog.get_logger(__name__)


def log_ranking_performance(results: list, query_time_ms: int, correlation_id: str) -> None:
    """Log performance metrics for ML ranking analysis."""
    if not results:
        return
    
    # Calculate ranking quality metrics
    avg_success_rate = sum(r["entry"]["success_rate"] for r in results) / len(results)
    avg_usage_count = sum(r["entry"]["usage_count"] for r in results) / len(results)
    avg_relevance_score = sum(r["relevance_score"] for r in results) / len(results)
    
    # Log ranking distribution
    score_distribution = {
        "high_relevance": len([r for r in results if r["relevance_score"] >= 0.7]),
        "medium_relevance": len([r for r in results if 0.4 <= r["relevance_score"] < 0.7]),
        "low_relevance": len([r for r in results if r["relevance_score"] < 0.4])
    }
    
    logger.info(
        "ML ranking performance metrics",
        correlation_id=correlation_id,
        service="fast-qa",
        avg_success_rate=round(avg_success_rate, 3),
        avg_usage_count=round(avg_usage_count, 1),
        avg_relevance_score=round(avg_relevance_score, 3),
        score_distribution=score_distribution,
        query_time_ms=query_time_ms,
        total_results=len(results)
    )


def calculate_relevance_score(entry, search_query: str, match_type: str) -> float:
    """
    Calculate enhanced relevance score using ML-derived success probability.
    
    Combines keyword relevance with machine learning insights from success rates
    and usage patterns to provide more effective search rankings.
    """
    # Base relevance from match type
    match_scores = {
        'exact_keyword': 0.4,
        'full_text': 0.3,
        'partial_text': 0.2,
        'fallback': 0.1
    }
    base_relevance = match_scores.get(match_type, 0.1)
    
    # Check if ML ranking is enabled
    if not fast_qa_config.FAST_QA_ML_RANKING_ENABLED:
        # Fallback to original simple ranking
        success_boost = entry.success_rate * 0.3
        usage_boost = min(entry.usage_count / 100.0, 0.2)
        return round(min(0.5 + success_boost + usage_boost + base_relevance, 1.0), 3)
    
    # ML-derived success probability
    # Uses success_rate as primary ML feature with usage_count as confidence indicator
    success_probability = entry.success_rate
    usage_confidence = min(entry.usage_count / 50.0, 1.0)  # Normalize usage count for confidence
    ml_score = success_probability * (0.7 + 0.3 * usage_confidence)  # Confidence-weighted success
    
    # Combine relevance and ML score using configurable weight
    ml_weight = fast_qa_config.FAST_QA_ML_RANKING_WEIGHT
    keyword_weight = 1.0 - ml_weight
    final_score = (ml_weight * ml_score) + (keyword_weight * base_relevance)
    
    # Apply recency boost for newer entries (small boost to avoid staleness)
    from datetime import datetime, timedelta
    if hasattr(entry, 'created_at') and entry.created_at:
        days_old = (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).days
        if days_old < 30:  # Boost entries less than 30 days old
            recency_boost = max(0.05 * (30 - days_old) / 30, 0.0)
            final_score = min(final_score + recency_boost, 1.0)
    
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
        
        # Log performance metrics for ML ranking analysis
        if results and fast_qa_config.FAST_QA_ML_RANKING_ENABLED:
            log_ranking_performance([r.dict() for r in results], query_time_ms, correlation_id)
        
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
            query_time_ms=query_time_ms,
            ml_ranking_enabled=fast_qa_config.FAST_QA_ML_RANKING_ENABLED,
            query_length=len(search_request.query),
            max_results_requested=search_request.max_results
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


@router.post("/feedback", response_model=APIResponse)
async def submit_qa_feedback(
    feedback_request: QAFeedbackRequest,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Submit feedback on Q&A solution helpfulness.
    
    Updates success rates using exponential moving average to improve
    future ML-based search rankings.
    """
    try:
        # Generate correlation ID if not provided
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A feedback received",
            correlation_id=correlation_id,
            service="fast-qa",
            solution_id=str(feedback_request.solution_id),
            is_helpful=feedback_request.is_helpful
        )
        
        # Process feedback to update success rate
        await qa_repo.update_success_rate(
            feedback_request.solution_id,
            feedback_request.is_helpful,
            correlation_id
        )
        
        logger.info(
            "Q&A feedback processed successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            solution_id=str(feedback_request.solution_id)
        )
        
        return {
            "data": {
                "message": "Feedback received successfully",
                "solution_id": str(feedback_request.solution_id),
                "is_helpful": feedback_request.is_helpful
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Q&A feedback submission failed",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e),
            solution_id=str(feedback_request.solution_id)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Feedback submission failed",
                "code": "FEEDBACK_ERROR"
            }
        )