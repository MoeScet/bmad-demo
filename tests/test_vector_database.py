"""
Test suite for vector database operations.

Validates ChromaDB integration, embedding operations, and search functionality
following BMAD testing standards and patterns.
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any

from shared.python.database import get_vector_client, VectorDatabaseError


class TestVectorDatabase:
    """Test suite for vector database operations"""

    @pytest.fixture
    async def vector_client(self):
        """Fixture providing vector database client"""
        async with get_vector_client() as client:
            yield client

    @pytest.fixture
    def test_collection_name(self):
        """Fixture providing unique test collection name"""
        return f"test_collection_{int(time.time())}"

    @pytest.fixture
    def sample_documents(self):
        """Fixture providing sample test documents"""
        return [
            "FastAPI is a modern web framework for building APIs with Python.",
            "ChromaDB provides vector database capabilities for semantic search.",
            "Docker containers enable consistent development environments.",
            "PostgreSQL is a powerful relational database management system.",
            "Railway platform simplifies cloud application deployment."
        ]

    @pytest.fixture
    def sample_metadatas(self):
        """Fixture providing sample metadata for documents"""
        return [
            {"category": "framework", "language": "python", "type": "web"},
            {"category": "database", "language": "python", "type": "vector"},
            {"category": "container", "language": "docker", "type": "deployment"},
            {"category": "database", "language": "sql", "type": "relational"},
            {"category": "platform", "language": "cloud", "type": "deployment"}
        ]

    @pytest.mark.asyncio
    async def test_connection_health(self, vector_client):
        """Test vector database connection and health check"""
        health_result = await vector_client.health_check()

        assert health_result["status"] == "healthy"
        assert "host" in health_result
        assert "port" in health_result
        assert "correlation_id" in health_result

    @pytest.mark.asyncio
    async def test_collection_creation(self, vector_client, test_collection_name):
        """Test collection creation and metadata"""
        metadata = {"description": "Test collection", "created_by": "test_suite"}

        collection_id = await vector_client.create_collection(
            test_collection_name,
            metadata=metadata
        )

        assert isinstance(collection_id, str)
        assert len(collection_id) > 0

        # Verify collection exists and has correct metadata
        info = await vector_client.get_collection_info(test_collection_name)
        assert info["name"] == test_collection_name
        assert info["count"] == 0  # No documents yet

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_embedding_operations(
        self,
        vector_client,
        test_collection_name,
        sample_documents,
        sample_metadatas
    ):
        """Test document embedding and storage operations"""
        # Create collection
        await vector_client.create_collection(test_collection_name)

        # Add embeddings
        doc_ids = await vector_client.add_embeddings(
            test_collection_name,
            sample_documents,
            metadatas=sample_metadatas
        )

        # Verify results
        assert len(doc_ids) == len(sample_documents)
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)

        # Verify collection count
        info = await vector_client.get_collection_info(test_collection_name)
        assert info["count"] == len(sample_documents)

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_similarity_search(
        self,
        vector_client,
        test_collection_name,
        sample_documents,
        sample_metadatas
    ):
        """Test semantic similarity search functionality"""
        # Setup test collection
        await vector_client.create_collection(test_collection_name)
        await vector_client.add_embeddings(
            test_collection_name,
            sample_documents,
            metadatas=sample_metadatas
        )

        # Test search
        search_query = "web development framework"
        results = await vector_client.search_similar(
            test_collection_name,
            search_query,
            n_results=3
        )

        # Verify search results structure
        assert "documents" in results
        assert "distances" in results
        assert "metadatas" in results
        assert "ids" in results

        # Verify result count
        assert len(results["documents"]) <= 3
        assert len(results["documents"]) == len(results["distances"])
        assert len(results["documents"]) == len(results["metadatas"])
        assert len(results["documents"]) == len(results["ids"])

        # Verify similarity scores (distances should be between 0 and 2 for cosine)
        assert all(0.0 <= distance <= 2.0 for distance in results["distances"])

        # Verify most relevant result (should be FastAPI document)
        if results["documents"]:
            top_result = results["documents"][0]
            assert "FastAPI" in top_result or "framework" in top_result.lower()

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_search_performance(
        self,
        vector_client,
        test_collection_name,
        sample_documents
    ):
        """Test search performance meets <2 second requirement"""
        # Setup larger test collection for performance testing
        await vector_client.create_collection(test_collection_name)

        # Add more documents for realistic performance test
        extended_docs = sample_documents * 20  # 100 documents
        await vector_client.add_embeddings(test_collection_name, extended_docs)

        # Test search performance
        search_query = "database management system"
        start_time = time.time()

        results = await vector_client.search_similar(
            test_collection_name,
            search_query,
            n_results=10
        )

        search_time = time.time() - start_time

        # Verify performance requirement
        assert search_time < 2.0, f"Search took {search_time:.3f}s (exceeds 2s limit)"
        assert len(results["documents"]) > 0, "Search should return results"

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_error_handling(self, vector_client):
        """Test error handling for various failure scenarios"""
        # Test search on non-existent collection
        with pytest.raises(VectorDatabaseError) as exc_info:
            await vector_client.search_similar(
                "non_existent_collection",
                "test query",
                n_results=5
            )

        # Verify error message contains fallback response
        error_message = str(exc_info.value).lower()
        assert "knowledge gap" in error_message

        # Test collection info on non-existent collection
        with pytest.raises(VectorDatabaseError):
            await vector_client.get_collection_info("non_existent_collection")

    @pytest.mark.asyncio
    async def test_metadata_filtering(
        self,
        vector_client,
        test_collection_name,
        sample_documents,
        sample_metadatas
    ):
        """Test metadata-based filtering in search"""
        # Setup test collection
        await vector_client.create_collection(test_collection_name)
        await vector_client.add_embeddings(
            test_collection_name,
            sample_documents,
            metadatas=sample_metadatas
        )

        # Test filtered search (database category only)
        results = await vector_client.search_similar(
            test_collection_name,
            "data storage",
            n_results=5,
            where={"category": "database"}
        )

        # Should only return database-related documents
        for metadata in results["metadatas"]:
            if metadata:  # Some results might have None metadata
                assert metadata.get("category") == "database"

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_batch_operations(self, vector_client, test_collection_name):
        """Test batch document operations"""
        # Create collection
        await vector_client.create_collection(test_collection_name)

        # Test batch insertion
        batch_size = 50
        documents = [f"Test document {i} for batch operations" for i in range(batch_size)]
        metadatas = [{"batch": "test", "index": i} for i in range(batch_size)]

        doc_ids = await vector_client.add_embeddings(
            test_collection_name,
            documents,
            metadatas=metadatas
        )

        assert len(doc_ids) == batch_size

        # Verify collection size
        info = await vector_client.get_collection_info(test_collection_name)
        assert info["count"] == batch_size

        # Test search across batch
        results = await vector_client.search_similar(
            test_collection_name,
            "batch operations",
            n_results=10
        )

        assert len(results["documents"]) > 0
        assert all("batch" in doc.lower() for doc in results["documents"])

        # Cleanup
        await vector_client.delete_collection(test_collection_name)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, vector_client):
        """Test concurrent vector database operations"""
        collection_names = [f"concurrent_test_{i}_{int(time.time())}" for i in range(3)]

        async def create_and_populate_collection(collection_name: str):
            """Helper function for concurrent testing"""
            await vector_client.create_collection(collection_name)
            documents = [f"Document in {collection_name}"]
            await vector_client.add_embeddings(collection_name, documents)
            return await vector_client.get_collection_info(collection_name)

        # Run concurrent operations
        tasks = [
            create_and_populate_collection(name)
            for name in collection_names
        ]

        results = await asyncio.gather(*tasks)

        # Verify all operations succeeded
        assert len(results) == len(collection_names)
        for result in results:
            assert result["count"] == 1

        # Cleanup
        for collection_name in collection_names:
            await vector_client.delete_collection(collection_name)

    @pytest.mark.asyncio
    async def test_correlation_id_propagation(self, vector_client, test_collection_name):
        """Test correlation ID propagation through operations"""
        correlation_id = "test-correlation-123"

        # Create collection with correlation ID
        await vector_client.create_collection(
            test_collection_name,
            correlation_id=correlation_id
        )

        # Add embeddings with correlation ID
        await vector_client.add_embeddings(
            test_collection_name,
            ["Test document for correlation ID"],
            correlation_id=correlation_id
        )

        # Search with correlation ID
        results = await vector_client.search_similar(
            test_collection_name,
            "test correlation",
            correlation_id=correlation_id
        )

        # Verify operations completed successfully
        assert len(results["documents"]) > 0

        # Health check with correlation ID
        health = await vector_client.health_check(correlation_id=correlation_id)
        assert health["correlation_id"] == correlation_id

        # Cleanup
        await vector_client.delete_collection(test_collection_name)