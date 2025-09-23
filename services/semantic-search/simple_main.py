"""
Simple Semantic Search Service

A simplified version that works with ChromaDB HTTP API
without requiring the ChromaDB Python client.
"""

import asyncio
import json
import time
import httpx
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# Simplified app without complex dependencies
app = FastAPI(
    title="BMAD Semantic Search Service",
    description="Vector-based semantic search using ChromaDB HTTP API",
    version="1.0.0"
)

# ChromaDB connection settings
CHROMADB_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_COLLECTION = "troubleshooting_docs_test"

# Request/Response Models
class SearchRequest(BaseModel):
    """Semantic search request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    collection_name: Optional[str] = Field(None, description="Collection to search")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity")

class SearchResult(BaseModel):
    """Individual search result"""
    document_id: str
    content: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """Semantic search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    collection_name: str
    status: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BMAD Semantic Search",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Service health check"""
    start_time = time.time()

    try:
        # Test ChromaDB connection
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CHROMADB_BASE_URL}/heartbeat")
            chromadb_healthy = response.status_code == 200
    except Exception:
        chromadb_healthy = False

    response_time = (time.time() - start_time) * 1000

    return {
        "data": {
            "service": "semantic-search",
            "status": "healthy" if chromadb_healthy else "degraded",
            "response_time_ms": round(response_time, 2),
            "dependencies": {
                "chromadb": "healthy" if chromadb_healthy else "unhealthy"
            }
        },
        "error": None
    }

@app.post("/api/v1/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search using ChromaDB HTTP API
    """
    start_time = time.time()
    collection_name = request.collection_name or DEFAULT_COLLECTION

    try:
        async with httpx.AsyncClient() as client:
            # Perform search via ChromaDB HTTP API
            search_response = await asyncio.wait_for(
                client.post(
                    f"{CHROMADB_BASE_URL}/collections/{collection_name}/query",
                    json={
                        "query_texts": [request.query],
                        "n_results": request.max_results
                    }
                ),
                timeout=10.0  # 10 second timeout
            )

            search_time = (time.time() - start_time) * 1000

            if search_response.status_code == 200:
                # Parse results
                data = search_response.json()
                documents = data.get("documents", [[]])[0]
                distances = data.get("distances", [[]])[0]
                metadatas = data.get("metadatas", [[]])[0]
                ids = data.get("ids", [[]])[0]

                # Convert to search results
                results = []
                for i, doc in enumerate(documents):
                    similarity = max(0, 1 - distances[i]) if i < len(distances) else 0.0

                    if similarity >= request.similarity_threshold:
                        results.append(SearchResult(
                            document_id=ids[i] if i < len(ids) else f"doc_{i}",
                            content=doc,
                            similarity_score=round(similarity, 4),
                            metadata=metadatas[i] if i < len(metadatas) else None
                        ))

                return SearchResponse(
                    query=request.query,
                    results=results,
                    total_results=len(results),
                    search_time_ms=round(search_time, 2),
                    collection_name=collection_name,
                    status="success"
                )

            elif search_response.status_code == 422:
                # ChromaDB still processing embeddings
                return SearchResponse(
                    query=request.query,
                    results=[],
                    total_results=0,
                    search_time_ms=round(search_time, 2),
                    collection_name=collection_name,
                    status="processing_embeddings"
                )

            else:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "message": "Vector database temporarily unavailable",
                        "chromadb_status": search_response.status_code
                    }
                )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail={"message": "Search request timed out"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal search error",
                "error": str(e)
            }
        )

@app.get("/api/v1/collections")
async def list_collections():
    """List available collections"""
    try:
        test_collections = [
            "troubleshooting_docs_test",
            "faq_content_test",
            "technical_examples_test"
        ]

        available_collections = []

        async with httpx.AsyncClient() as client:
            for collection in test_collections:
                try:
                    response = await client.get(f"{CHROMADB_BASE_URL}/collections/{collection}")
                    if response.status_code == 200:
                        info = response.json()
                        available_collections.append({
                            "name": collection,
                            "document_count": info.get("count", 0),
                            "metadata": info.get("metadata", {})
                        })
                except Exception:
                    continue

        return {
            "data": available_collections,
            "error": None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to list collections",
                "error": str(e)
            }
        )

@app.get("/api/v1/test")
async def test_search():
    """Test endpoint with sample searches"""
    test_queries = [
        "network connectivity problems",
        "password reset help",
        "database performance optimization"
    ]

    results = []

    for query in test_queries:
        try:
            # Use internal search function
            search_request = SearchRequest(
                query=query,
                max_results=3,
                similarity_threshold=0.5
            )

            result = await semantic_search(search_request)
            results.append({
                "query": query,
                "status": result.status,
                "results_found": result.total_results,
                "search_time_ms": result.search_time_ms
            })

        except Exception as e:
            results.append({
                "query": query,
                "status": "error",
                "error": str(e)
            })

    return {
        "data": {
            "test_results": results,
            "summary": f"{len([r for r in results if r.get('status') != 'error'])}/{len(results)} queries successful"
        },
        "error": None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)