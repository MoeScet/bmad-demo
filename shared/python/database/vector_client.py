"""
ChromaDB Vector Database Client

Provides async interface for vector database operations with error handling
and fallback responses following coding standards.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import uuid

import chromadb
from chromadb.config import Settings
from chromadb.errors import ChromaError
from sentence_transformers import SentenceTransformer
import numpy as np

from ..config.base import get_settings


logger = logging.getLogger(__name__)


class VectorDatabaseError(Exception):
    """Custom exception for vector database operations"""
    pass


class ChromaDBClient:
    """
    Async ChromaDB client with error handling and fallback responses.

    Follows coding standards:
    - Vector Database Isolation: ChromaDB operations wrapped in try/catch with fallback
    - Response Time Budget: <2 second target for vector similarity search
    - Async Patterns: async/await for all I/O operations
    - Correlation ID Propagation: Every operation supports correlation_id
    """

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self._client = None
        self._embedding_model = None
        self._embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

    async def initialize(self) -> None:
        """Initialize ChromaDB client and embedding model"""
        try:
            # Initialize ChromaDB client
            self._client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    chroma_client_auth_provider=None,
                    chroma_client_auth_credentials=None,
                )
            )

            # Test connection
            await self._test_connection()

            # Initialize embedding model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._embedding_model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self._embedding_model_name)
            )

            logger.info(
                "ChromaDB client initialized successfully",
                extra={"host": self.host, "port": self.port}
            )

        except Exception as e:
            logger.error(
                "Failed to initialize ChromaDB client",
                extra={"error": str(e), "host": self.host, "port": self.port}
            )
            raise VectorDatabaseError(f"ChromaDB initialization failed: {str(e)}")

    async def _test_connection(self) -> None:
        """Test ChromaDB connection with timeout"""
        try:
            # Run heartbeat in executor to make it async
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, self._client.heartbeat),
                timeout=2.0  # 2 second timeout per coding standards
            )
        except asyncio.TimeoutError:
            raise VectorDatabaseError("ChromaDB connection timeout")
        except Exception as e:
            raise VectorDatabaseError(f"ChromaDB connection failed: {str(e)}")

    async def create_collection(
        self,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Create a new collection with optional metadata

        Args:
            collection_name: Name of the collection
            metadata: Optional metadata for the collection
            correlation_id: Request correlation ID for tracing

        Returns:
            Collection ID

        Raises:
            VectorDatabaseError: If operation fails with fallback response
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            loop = asyncio.get_event_loop()
            collection = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.create_collection(
                        name=collection_name,
                        metadata=metadata or {}
                    )
                ),
                timeout=2.0
            )

            logger.info(
                "Collection created successfully",
                extra={
                    "collection_name": collection_name,
                    "correlation_id": correlation_id
                }
            )

            return collection.id

        except asyncio.TimeoutError:
            logger.error(
                "Collection creation timeout",
                extra={
                    "collection_name": collection_name,
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database timeout")

        except ChromaError as e:
            logger.error(
                "ChromaDB error during collection creation",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database unavailable")

        except Exception as e:
            logger.error(
                "Unexpected error during collection creation",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database error")

    async def add_embeddings(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Add documents to collection with auto-generated embeddings

        Args:
            collection_name: Name of the collection
            documents: List of documents to embed and add
            metadatas: Optional metadata for each document
            ids: Optional custom IDs, auto-generated if not provided
            correlation_id: Request correlation ID for tracing

        Returns:
            List of document IDs
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        document_ids = ids or [str(uuid.uuid4()) for _ in documents]

        try:
            # Generate embeddings
            loop = asyncio.get_event_loop()
            embeddings = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._embedding_model.encode(documents).tolist()
                ),
                timeout=10.0  # Longer timeout for embedding generation
            )

            # Add to collection
            collection = await loop.run_in_executor(
                None,
                lambda: self._client.get_collection(collection_name)
            )

            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: collection.add(
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas or [{}] * len(documents),
                        ids=document_ids
                    )
                ),
                timeout=2.0
            )

            logger.info(
                "Documents added to collection successfully",
                extra={
                    "collection_name": collection_name,
                    "document_count": len(documents),
                    "correlation_id": correlation_id
                }
            )

            return document_ids

        except asyncio.TimeoutError:
            logger.error(
                "Add embeddings operation timeout",
                extra={
                    "collection_name": collection_name,
                    "document_count": len(documents),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - embedding operation timeout")

        except Exception as e:
            logger.error(
                "Error adding embeddings to collection",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database error")

    async def search_similar(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents in collection

        Args:
            collection_name: Name of the collection to search
            query: Query text to find similar documents
            n_results: Number of results to return
            where: Optional metadata filter
            correlation_id: Request correlation ID for tracing

        Returns:
            Dictionary with search results including documents, distances, metadatas
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            loop = asyncio.get_event_loop()

            # Generate query embedding
            query_embedding = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._embedding_model.encode([query]).tolist()[0]
                ),
                timeout=2.0
            )

            # Search collection
            collection = await loop.run_in_executor(
                None,
                lambda: self._client.get_collection(collection_name)
            )

            results = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results,
                        where=where
                    )
                ),
                timeout=2.0  # <2 second target per coding standards
            )

            logger.info(
                "Similarity search completed successfully",
                extra={
                    "collection_name": collection_name,
                    "query_length": len(query),
                    "results_count": len(results['ids'][0]) if results['ids'] else 0,
                    "correlation_id": correlation_id
                }
            )

            return {
                "documents": results.get("documents", [[]])[0],
                "distances": results.get("distances", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "ids": results.get("ids", [[]])[0]
            }

        except asyncio.TimeoutError:
            logger.error(
                "Similarity search timeout",
                extra={
                    "collection_name": collection_name,
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - search operation timeout")

        except Exception as e:
            logger.error(
                "Error during similarity search",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database error")

    async def get_collection_info(
        self,
        collection_name: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get collection information including count and metadata"""
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            loop = asyncio.get_event_loop()
            collection = await loop.run_in_executor(
                None,
                lambda: self._client.get_collection(collection_name)
            )

            count = await asyncio.wait_for(
                loop.run_in_executor(None, collection.count),
                timeout=2.0
            )

            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }

        except Exception as e:
            logger.error(
                "Error getting collection info",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database error")

    async def delete_collection(
        self,
        collection_name: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Delete a collection"""
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.delete_collection(collection_name)
                ),
                timeout=2.0
            )

            logger.info(
                "Collection deleted successfully",
                extra={
                    "collection_name": collection_name,
                    "correlation_id": correlation_id
                }
            )

            return True

        except Exception as e:
            logger.error(
                "Error deleting collection",
                extra={
                    "collection_name": collection_name,
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )
            raise VectorDatabaseError("knowledge gap - vector database error")

    async def health_check(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform health check on ChromaDB connection

        Returns:
            Dictionary with health status and connection info
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            await self._test_connection()

            return {
                "status": "healthy",
                "host": self.host,
                "port": self.port,
                "correlation_id": correlation_id
            }

        except VectorDatabaseError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.host,
                "port": self.port,
                "correlation_id": correlation_id
            }


@asynccontextmanager
async def get_vector_client(
    host: Optional[str] = None,
    port: Optional[int] = None
):
    """
    Async context manager for ChromaDB client

    Usage:
        async with get_vector_client() as client:
            await client.create_collection("test_collection")
    """
    settings = get_settings()
    client = ChromaDBClient(
        host=host or settings.CHROMA_HOST,
        port=port or settings.CHROMA_PORT
    )

    await client.initialize()

    try:
        yield client
    finally:
        # Cleanup if needed
        pass