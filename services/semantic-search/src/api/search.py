"""
Semantic Search API Endpoints

REST API endpoints for vector-based semantic search operations
with proper error handling and performance monitoring.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel, Field, validator

from ..config.settings import get_settings
from shared.python.database import get_vector_client, VectorDatabaseError


logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class SearchRequest(BaseModel):
    """Semantic search request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    collection_name: Optional[str] = Field(None, description="Collection to search (defaults to service collection)")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results to return")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_metadata: bool = Field(True, description="Include document metadata in results")

    @validator("query")
    def validate_query(cls, v):
        """Validate query is not just whitespace"""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class SearchResult(BaseModel):
    """Individual search result"""
    document_id: str = Field(..., description="Document identifier")
    content: str = Field(..., description="Document content")
    similarity_score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class SearchResponse(BaseModel):
    """Semantic search response model"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")
    collection_name: str = Field(..., description="Collection that was searched")
    correlation_id: str = Field(..., description="Request correlation ID")


class CollectionInfo(BaseModel):
    """Collection information model"""
    name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Number of documents in collection")
    metadata: Dict[str, Any] = Field(..., description="Collection metadata")


# API Endpoints
@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    http_request: Request,
    settings: get_settings = Depends()
) -> SearchResponse:
    """
    Perform semantic search using vector similarity

    Searches for documents similar to the provided query using
    ChromaDB vector similarity with sentence-transformers embeddings.
    """
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()

    logger.info(
        "Semantic search request received",
        extra={
            "query_length": len(request.query),
            "max_results": request.max_results,
            "correlation_id": correlation_id
        }
    )

    try:
        # Use default collection if not specified
        collection_name = request.collection_name or settings.DEFAULT_COLLECTION

        # Perform search with timeout
        async with get_vector_client(settings.CHROMA_HOST, settings.CHROMA_PORT) as client:
            search_results = await asyncio.wait_for(
                client.search_similar(
                    collection_name=collection_name,
                    query=request.query,
                    n_results=request.max_results,
                    correlation_id=correlation_id
                ),
                timeout=settings.SEMANTIC_SEARCH_TIMEOUT
            )

        # Process results
        results = []
        for i, doc in enumerate(search_results["documents"]):
            similarity_score = 1.0 - search_results["distances"][i]  # Convert distance to similarity

            # Apply similarity threshold filter
            if similarity_score >= request.similarity_threshold:
                result = SearchResult(
                    document_id=search_results["ids"][i],
                    content=doc,
                    similarity_score=round(similarity_score, 4),
                    metadata=search_results["metadatas"][i] if request.include_metadata else None
                )
                results.append(result)

        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        logger.info(
            "Semantic search completed successfully",
            extra={
                "results_count": len(results),
                "search_time_ms": search_time,
                "collection_name": collection_name,
                "correlation_id": correlation_id
            }
        )

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2),
            collection_name=collection_name,
            correlation_id=correlation_id
        )

    except asyncio.TimeoutError:
        logger.error(
            "Semantic search timeout",
            extra={
                "timeout_seconds": settings.SEMANTIC_SEARCH_TIMEOUT,
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=504,
            detail={
                "message": "Search request timed out",
                "correlation_id": correlation_id
            }
        )

    except VectorDatabaseError as e:
        logger.error(
            "Vector database error during search",
            extra={
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Search service temporarily unavailable",
                "correlation_id": correlation_id
            }
        )

    except Exception as e:
        logger.error(
            "Unexpected error during semantic search",
            extra={
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal search error occurred",
                "correlation_id": correlation_id
            }
        )


@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections(
    http_request: Request,
    settings: get_settings = Depends()
) -> List[CollectionInfo]:
    """List available collections for searching"""
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    try:
        async with get_vector_client(settings.CHROMA_HOST, settings.CHROMA_PORT) as client:
            # Get default collection info (in real implementation, list all collections)
            collection_info = await client.get_collection_info(
                settings.DEFAULT_COLLECTION,
                correlation_id=correlation_id
            )

            return [
                CollectionInfo(
                    name=collection_info["name"],
                    document_count=collection_info["count"],
                    metadata=collection_info["metadata"]
                )
            ]

    except VectorDatabaseError as e:
        logger.error(
            "Error listing collections",
            extra={
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Collection service temporarily unavailable",
                "correlation_id": correlation_id
            }
        )

    except Exception as e:
        logger.error(
            "Unexpected error listing collections",
            extra={
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal service error",
                "correlation_id": correlation_id
            }
        )


@router.get("/collections/{collection_name}/info", response_model=CollectionInfo)
async def get_collection_info(
    collection_name: str,
    http_request: Request,
    settings: get_settings = Depends()
) -> CollectionInfo:
    """Get information about a specific collection"""
    correlation_id = http_request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    try:
        async with get_vector_client(settings.CHROMA_HOST, settings.CHROMA_PORT) as client:
            collection_info = await client.get_collection_info(
                collection_name,
                correlation_id=correlation_id
            )

            return CollectionInfo(
                name=collection_info["name"],
                document_count=collection_info["count"],
                metadata=collection_info["metadata"]
            )

    except VectorDatabaseError as e:
        logger.error(
            "Error getting collection info",
            extra={
                "collection_name": collection_name,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Collection '{collection_name}' not found or unavailable",
                "correlation_id": correlation_id
            }
        )

    except Exception as e:
        logger.error(
            "Unexpected error getting collection info",
            extra={
                "collection_name": collection_name,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal service error",
                "correlation_id": correlation_id
            }
        )