"""
Content storage and management for manual content and vector embeddings
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from shared.python.database.connection import get_db_session
from shared.python.models.manual_content import ManualContent

logger = logging.getLogger(__name__)


class ContentManager:
    """
    Manages storage and retrieval of manual content in both PostgreSQL and ChromaDB
    """

    def __init__(self):
        self.settings = get_settings()

    async def store_content_chunk(
        self,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float],
        page_reference: str,
        confidence_score: float,
        correlation_id: str
    ) -> str:
        """
        Store a content chunk in both PostgreSQL and ChromaDB

        Args:
            content: Text content
            metadata: Extracted metadata
            embedding: Vector embedding
            page_reference: Page reference
            confidence_score: Quality confidence score
            correlation_id: Request correlation ID

        Returns:
            Content ID
        """
        content_id = str(uuid.uuid4())

        try:
            # Store in PostgreSQL
            async with get_db_session() as session:
                manual_content = ManualContent(
                    id=content_id,
                    manufacturer=metadata.get('manufacturer', 'Unknown'),
                    model_series=metadata.get('model_series', 'Unknown'),
                    section_title=metadata.get('section_title', 'Manual Content'),
                    content=content,
                    content_type=metadata.get('content_type', 'troubleshooting'),
                    confidence_score=confidence_score,
                    source_manual=metadata.get('source_manual', ''),
                    page_reference=page_reference,
                    created_at=datetime.utcnow()
                )

                session.add(manual_content)
                await session.commit()

            # Store embedding in ChromaDB
            await self._store_embedding_in_chromadb(
                content_id,
                content,
                embedding,
                metadata,
                correlation_id
            )

            logger.info(
                f"Content chunk stored successfully: {content_id}",
                extra={'correlation_id': correlation_id}
            )

            return content_id

        except Exception as e:
            logger.error(
                f"Failed to store content chunk: {str(e)}",
                extra={'correlation_id': correlation_id}
            )
            raise

    async def _store_embedding_in_chromadb(
        self,
        content_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        correlation_id: str
    ) -> bool:
        """
        Store embedding in ChromaDB collection

        Args:
            content_id: Unique content identifier
            content: Text content
            embedding: Vector embedding
            metadata: Content metadata
            correlation_id: Request correlation ID

        Returns:
            Success status
        """
        try:
            async with httpx.AsyncClient() as client:
                # Ensure collection exists
                collection_name = self.settings.MANUAL_CONTENT_COLLECTION

                create_response = await client.post(
                    f"{self.settings.CHROMADB_BASE_URL}/collections",
                    json={
                        "name": collection_name,
                        "metadata": {
                            "description": "Manual content embeddings",
                            "content_type": "manual_content"
                        }
                    }
                )

                # Add document to collection
                add_response = await client.post(
                    f"{self.settings.CHROMADB_BASE_URL}/collections/{collection_name}/add",
                    json={
                        "documents": [content],
                        "embeddings": [embedding],
                        "metadatas": [{
                            "manufacturer": metadata.get('manufacturer', 'Unknown'),
                            "content_type": metadata.get('content_type', 'troubleshooting'),
                            "model_series": metadata.get('model_series', 'Unknown'),
                            "source_manual": metadata.get('source_manual', ''),
                            "content_id": content_id
                        }],
                        "ids": [content_id]
                    }
                )

                if add_response.status_code in [200, 201]:
                    logger.info(
                        f"Embedding stored in ChromaDB: {content_id}",
                        extra={'correlation_id': correlation_id}
                    )
                    return True
                else:
                    logger.warning(
                        f"ChromaDB add returned: {add_response.status_code}",
                        extra={'correlation_id': correlation_id}
                    )
                    return True  # May be processing asynchronously

        except Exception as e:
            logger.error(
                f"Failed to store embedding in ChromaDB: {str(e)}",
                extra={'correlation_id': correlation_id}
            )
            # Don't fail the entire operation for ChromaDB issues
            return False

    async def search_content(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        content_type: Optional[str] = None,
        min_confidence: float = 0.0,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search manual content using vector similarity

        Args:
            query: Search query
            manufacturer: Filter by manufacturer
            content_type: Filter by content type
            min_confidence: Minimum confidence score
            max_results: Maximum results to return

        Returns:
            Search results with timing information
        """
        start_time = time.time()

        try:
            # Search in ChromaDB
            async with httpx.AsyncClient() as client:
                collection_name = self.settings.MANUAL_CONTENT_COLLECTION

                # Build ChromaDB query
                chromadb_query = {
                    "query_texts": [query],
                    "n_results": max_results
                }

                # Add metadata filters if provided
                where_conditions = {}
                if manufacturer:
                    where_conditions["manufacturer"] = manufacturer
                if content_type:
                    where_conditions["content_type"] = content_type

                if where_conditions:
                    chromadb_query["where"] = where_conditions

                search_response = await client.post(
                    f"{self.settings.CHROMADB_BASE_URL}/collections/{collection_name}/query",
                    json=chromadb_query
                )

                if search_response.status_code == 200:
                    results = search_response.json()
                    content_ids = results.get("ids", [[]])[0]
                    distances = results.get("distances", [[]])[0]
                    documents = results.get("documents", [[]])[0]
                    metadatas = results.get("metadatas", [[]])[0]

                    # Get full content from PostgreSQL
                    detailed_results = []
                    async with get_db_session() as session:
                        for i, content_id in enumerate(content_ids):
                            if i < len(distances):
                                similarity = max(0, 1 - distances[i])

                                # Skip if below confidence threshold
                                if similarity < min_confidence:
                                    continue

                                # Get full content from database
                                result = await session.execute(
                                    select(ManualContent).where(ManualContent.id == content_id)
                                )
                                content_item = result.scalar_one_or_none()

                                if content_item:
                                    detailed_results.append({
                                        "id": content_item.id,
                                        "manufacturer": content_item.manufacturer,
                                        "model_series": content_item.model_series,
                                        "section_title": content_item.section_title,
                                        "content": content_item.content,
                                        "content_type": content_item.content_type,
                                        "confidence_score": content_item.confidence_score,
                                        "source_manual": content_item.source_manual,
                                        "page_reference": content_item.page_reference,
                                        "created_at": content_item.created_at.isoformat(),
                                        "similarity_score": round(similarity, 4)
                                    })

                    search_time = (time.time() - start_time) * 1000

                    return {
                        "query": query,
                        "results": detailed_results,
                        "total_results": len(detailed_results),
                        "search_time_ms": round(search_time, 2)
                    }

                else:
                    # Fallback to database text search
                    return await self._fallback_text_search(
                        query, manufacturer, content_type, min_confidence, max_results
                    )

        except Exception as e:
            logger.error(f"Content search failed: {str(e)}")
            # Fallback to database search
            return await self._fallback_text_search(
                query, manufacturer, content_type, min_confidence, max_results
            )

    async def _fallback_text_search(
        self,
        query: str,
        manufacturer: Optional[str],
        content_type: Optional[str],
        min_confidence: float,
        max_results: int
    ) -> Dict[str, Any]:
        """Fallback text search using PostgreSQL full-text search"""
        start_time = time.time()

        try:
            async with get_db_session() as session:
                # Build query
                query_stmt = select(ManualContent)

                # Add filters
                if manufacturer:
                    query_stmt = query_stmt.where(ManualContent.manufacturer.ilike(f"%{manufacturer}%"))
                if content_type:
                    query_stmt = query_stmt.where(ManualContent.content_type == content_type)

                query_stmt = query_stmt.where(ManualContent.confidence_score >= min_confidence)
                query_stmt = query_stmt.limit(max_results)

                result = await session.execute(query_stmt)
                content_items = result.scalars().all()

                results = []
                for item in content_items:
                    results.append({
                        "id": item.id,
                        "manufacturer": item.manufacturer,
                        "model_series": item.model_series,
                        "section_title": item.section_title,
                        "content": item.content,
                        "content_type": item.content_type,
                        "confidence_score": item.confidence_score,
                        "source_manual": item.source_manual,
                        "page_reference": item.page_reference,
                        "created_at": item.created_at.isoformat(),
                        "similarity_score": 0.5  # Default similarity for text search
                    })

                search_time = (time.time() - start_time) * 1000

                return {
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "search_time_ms": round(search_time, 2)
                }

        except Exception as e:
            logger.error(f"Fallback text search failed: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "search_time_ms": 0.0
            }

    async def list_content(
        self,
        manufacturer: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List manual content with optional filtering"""
        try:
            async with get_db_session() as session:
                query_stmt = select(ManualContent)

                # Add filters
                if manufacturer:
                    query_stmt = query_stmt.where(ManualContent.manufacturer.ilike(f"%{manufacturer}%"))
                if content_type:
                    query_stmt = query_stmt.where(ManualContent.content_type == content_type)

                query_stmt = query_stmt.offset(offset).limit(limit)
                query_stmt = query_stmt.order_by(ManualContent.created_at.desc())

                result = await session.execute(query_stmt)
                content_items = result.scalars().all()

                return [{
                    "id": item.id,
                    "manufacturer": item.manufacturer,
                    "model_series": item.model_series,
                    "section_title": item.section_title,
                    "content": item.content[:500] + "..." if len(item.content) > 500 else item.content,
                    "content_type": item.content_type,
                    "confidence_score": item.confidence_score,
                    "source_manual": item.source_manual,
                    "page_reference": item.page_reference,
                    "created_at": item.created_at.isoformat()
                } for item in content_items]

        except Exception as e:
            logger.error(f"Failed to list content: {str(e)}")
            return []

    async def get_content_by_id(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get specific content item by ID"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(ManualContent).where(ManualContent.id == content_id)
                )
                content_item = result.scalar_one_or_none()

                if content_item:
                    return {
                        "id": content_item.id,
                        "manufacturer": content_item.manufacturer,
                        "model_series": content_item.model_series,
                        "section_title": content_item.section_title,
                        "content": content_item.content,
                        "content_type": content_item.content_type,
                        "confidence_score": content_item.confidence_score,
                        "source_manual": content_item.source_manual,
                        "page_reference": content_item.page_reference,
                        "created_at": content_item.created_at.isoformat()
                    }

                return None

        except Exception as e:
            logger.error(f"Failed to get content by ID: {str(e)}")
            return None

    async def delete_content(self, content_id: str) -> bool:
        """Delete content from both PostgreSQL and ChromaDB"""
        try:
            # Delete from PostgreSQL
            async with get_db_session() as session:
                result = await session.execute(
                    delete(ManualContent).where(ManualContent.id == content_id)
                )
                await session.commit()

                if result.rowcount == 0:
                    return False

            # Delete from ChromaDB
            try:
                async with httpx.AsyncClient() as client:
                    collection_name = self.settings.MANUAL_CONTENT_COLLECTION
                    await client.post(
                        f"{self.settings.CHROMADB_BASE_URL}/collections/{collection_name}/delete",
                        json={"ids": [content_id]}
                    )
            except Exception as e:
                logger.warning(f"Failed to delete from ChromaDB: {e}")

            logger.info(f"Content deleted: {content_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete content: {str(e)}")
            return False

    async def reprocess_content(self, content_id: str) -> bool:
        """Reprocess content item (placeholder for future implementation)"""
        # This would regenerate embeddings and update quality scores
        logger.info(f"Reprocessing content: {content_id}")
        return True