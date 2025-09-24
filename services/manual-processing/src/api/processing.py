"""
Processing management API endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

from ..processing.content_manager import ContentManager
from ..processing.quality_validator import QualityValidator

logger = logging.getLogger(__name__)
router = APIRouter()


class ManualContentItem(BaseModel):
    """Manual content item model"""
    id: str
    manufacturer: str
    model_series: str
    section_title: str
    content: str
    content_type: str
    confidence_score: float
    source_manual: str
    page_reference: str = None
    created_at: datetime


class ContentSearchRequest(BaseModel):
    """Content search request model"""
    query: str
    manufacturer: Optional[str] = None
    content_type: Optional[str] = None
    min_confidence: float = 0.0
    max_results: int = 10


class ContentSearchResponse(BaseModel):
    """Content search response model"""
    query: str
    results: List[ManualContentItem]
    total_results: int
    search_time_ms: float


@router.get("/content")
async def list_manual_content(
    request: Request,
    manufacturer: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    List manual content with optional filtering
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        content_manager = ContentManager()
        results = await content_manager.list_content(
            manufacturer=manufacturer,
            content_type=content_type,
            limit=limit,
            offset=offset
        )

        return {
            "data": {
                "content": results,
                "total_count": len(results),
                "limit": limit,
                "offset": offset
            },
            "error": None
        }

    except Exception as e:
        logger.error(
            f"Failed to list content: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve content",
                "correlation_id": correlation_id
            }
        )


@router.post("/content/search", response_model=ContentSearchResponse)
async def search_manual_content(
    request: Request,
    search_request: ContentSearchRequest
) -> Dict[str, Any]:
    """
    Search manual content using text similarity
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        content_manager = ContentManager()
        results = await content_manager.search_content(
            query=search_request.query,
            manufacturer=search_request.manufacturer,
            content_type=search_request.content_type,
            min_confidence=search_request.min_confidence,
            max_results=search_request.max_results
        )

        return {
            "data": results,
            "error": None
        }

    except Exception as e:
        logger.error(
            f"Content search failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Content search failed",
                "correlation_id": correlation_id
            }
        )


@router.get("/content/{content_id}")
async def get_manual_content(
    content_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Get specific manual content item
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        content_manager = ContentManager()
        content = await content_manager.get_content_by_id(content_id)

        if not content:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Content not found",
                    "correlation_id": correlation_id
                }
            )

        return {
            "data": content,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get content: {str(e)}",
            extra={'correlation_id': correlation_id, 'content_id': content_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve content",
                "correlation_id": correlation_id
            }
        )


@router.delete("/content/{content_id}")
async def delete_manual_content(
    content_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Delete manual content item
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        content_manager = ContentManager()
        success = await content_manager.delete_content(content_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Content not found",
                    "correlation_id": correlation_id
                }
            )

        return {
            "data": {
                "message": "Content deleted successfully",
                "content_id": content_id
            },
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete content: {str(e)}",
            extra={'correlation_id': correlation_id, 'content_id': content_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to delete content",
                "correlation_id": correlation_id
            }
        )


@router.post("/content/{content_id}/reprocess")
async def reprocess_content(
    content_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Reprocess content item (regenerate embeddings, re-validate)
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        content_manager = ContentManager()
        success = await content_manager.reprocess_content(content_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Content not found",
                    "correlation_id": correlation_id
                }
            )

        return {
            "data": {
                "message": "Content reprocessing initiated",
                "content_id": content_id
            },
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to reprocess content: {str(e)}",
            extra={'correlation_id': correlation_id, 'content_id': content_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to reprocess content",
                "correlation_id": correlation_id
            }
        )


@router.get("/quality/report")
async def get_quality_report(request: Request) -> Dict[str, Any]:
    """
    Get quality report for all processed content
    """
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    try:
        validator = QualityValidator()
        report = await validator.generate_quality_report()

        return {
            "data": report,
            "error": None
        }

    except Exception as e:
        logger.error(
            f"Failed to generate quality report: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to generate quality report",
                "correlation_id": correlation_id
            }
        )