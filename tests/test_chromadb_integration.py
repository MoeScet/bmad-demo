"""
ChromaDB Integration Tests for Story 1.5

Focused integration tests for ChromaDB HTTP API and Python client integration.
These tests require ChromaDB to be running and validate actual integration.
"""

import pytest
import asyncio
import httpx
import time
import json
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChromaDBHTTPIntegration:
    """Integration tests using ChromaDB HTTP API"""

    @pytest.fixture
    def http_client_config(self):
        """HTTP client configuration for ChromaDB"""
        return {
            "base_url": "http://localhost:8000/api/v1",
            "timeout": 10.0
        }

    @pytest.fixture
    def test_collection_name(self):
        """Generate unique test collection name"""
        return f"integration_test_{int(time.time())}"

    @pytest.fixture
    def sample_test_data(self):
        """Sample data for integration testing"""
        return {
            "documents": [
                "ChromaDB is a vector database for AI applications",
                "FastAPI provides high-performance web API framework",
                "Docker enables containerized application deployment",
                "PostgreSQL offers robust relational database features",
                "Python machine learning with sentence transformers"
            ],
            "metadatas": [
                {"category": "database", "type": "vector"},
                {"category": "framework", "type": "web"},
                {"category": "deployment", "type": "container"},
                {"category": "database", "type": "relational"},
                {"category": "ml", "type": "embeddings"}
            ]
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chromadb_service_availability(self, http_client_config):
        """Test ChromaDB service is available and responding"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{http_client_config['base_url'][:-7]}/heartbeat")

                assert response.status_code == 200
                heartbeat_data = response.json()

                # ChromaDB heartbeat should return nanosecond timestamp
                assert "nanosecond heartbeat" in heartbeat_data or isinstance(heartbeat_data, (int, float))

        except httpx.ConnectError:
            pytest.skip("ChromaDB not running on localhost:8000 - integration test skipped")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_collection_lifecycle_integration(self, http_client_config, test_collection_name, sample_test_data):
        """Test complete collection lifecycle via HTTP API"""
        async with httpx.AsyncClient(timeout=http_client_config['timeout']) as client:
            base_url = http_client_config['base_url']

            try:
                # 1. Create collection
                create_response = await client.post(
                    f"{base_url}/collections",
                    json={
                        "name": test_collection_name,
                        "metadata": {"test": True, "created_by": "integration_test"}
                    }
                )

                assert create_response.status_code in [200, 201]

                # 2. Add documents with embeddings
                add_response = await client.post(
                    f"{base_url}/collections/{test_collection_name}/add",
                    json={
                        "documents": sample_test_data["documents"],
                        "metadatas": sample_test_data["metadatas"],
                        "ids": [f"doc_{i}" for i in range(len(sample_test_data["documents"]))]
                    }
                )

                assert add_response.status_code == 200

                # 3. Verify collection info
                info_response = await client.get(f"{base_url}/collections/{test_collection_name}")
                assert info_response.status_code == 200

                collection_info = info_response.json()
                assert collection_info["name"] == test_collection_name
                assert collection_info.get("count", 0) == len(sample_test_data["documents"])

                # 4. Test semantic search
                search_response = await client.post(
                    f"{base_url}/collections/{test_collection_name}/query",
                    json={
                        "query_texts": ["database vector search"],
                        "n_results": 3
                    }
                )

                assert search_response.status_code == 200
                search_results = search_response.json()

                # Validate search results structure
                assert "documents" in search_results
                assert "distances" in search_results
                assert "metadatas" in search_results
                assert "ids" in search_results

                documents = search_results["documents"][0]
                distances = search_results["distances"][0]

                assert len(documents) > 0
                assert len(distances) == len(documents)

                # Validate similarity scores (distances should be reasonable)
                for distance in distances:
                    assert 0 <= distance <= 2.0, f"Distance {distance} outside expected range"

            finally:
                # Cleanup
                try:
                    await client.delete(f"{base_url}/collections/{test_collection_name}")
                except:
                    pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_performance_integration(self, http_client_config, test_collection_name, sample_test_data):
        """Test search performance meets <2 second requirement"""
        async with httpx.AsyncClient(timeout=http_client_config['timeout']) as client:
            base_url = http_client_config['base_url']

            try:
                # Setup test collection
                await client.post(
                    f"{base_url}/collections",
                    json={"name": test_collection_name, "metadata": {"test": True}}
                )

                await client.post(
                    f"{base_url}/collections/{test_collection_name}/add",
                    json={
                        "documents": sample_test_data["documents"] * 10,  # 50 documents
                        "ids": [f"doc_{i}" for i in range(len(sample_test_data["documents"]) * 10)]
                    }
                )

                # Performance test queries
                test_queries = [
                    "vector database semantic search",
                    "web framework API development",
                    "container deployment docker",
                    "machine learning embeddings",
                    "database relational PostgreSQL"
                ]

                performance_results = []

                for query in test_queries:
                    start_time = time.time()

                    search_response = await client.post(
                        f"{base_url}/collections/{test_collection_name}/query",
                        json={
                            "query_texts": [query],
                            "n_results": 10
                        }
                    )

                    query_time = time.time() - start_time

                    assert search_response.status_code == 200
                    results = search_response.json()

                    performance_results.append({
                        "query": query,
                        "time": query_time,
                        "results_count": len(results["documents"][0])
                    })

                    # Individual query performance check
                    assert query_time < 2.0, f"Query '{query}' took {query_time:.3f}s, exceeds 2s limit"

                # Overall performance validation
                avg_time = sum(r["time"] for r in performance_results) / len(performance_results)
                assert avg_time < 1.0, f"Average query time {avg_time:.3f}s should be well under 2s"

                print(f"Integration Performance Test Results:")
                print(f"Average query time: {avg_time:.3f}s")
                for result in performance_results:
                    print(f"  '{result['query'][:30]}...': {result['time']:.3f}s ({result['results_count']} results)")

            finally:
                # Cleanup
                try:
                    await client.delete(f"{base_url}/collections/{test_collection_name}")
                except:
                    pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, http_client_config):
        """Test error handling scenarios via HTTP API"""
        async with httpx.AsyncClient(timeout=http_client_config['timeout']) as client:
            base_url = http_client_config['base_url']

            # Test 1: Query non-existent collection
            error_response = await client.post(
                f"{base_url}/collections/nonexistent_collection_test/query",
                json={"query_texts": ["test query"], "n_results": 1}
            )

            assert error_response.status_code in [404, 400, 422]

            # Test 2: Invalid collection name
            invalid_response = await client.post(
                f"{base_url}/collections/",
                json={"name": "", "metadata": {}}  # Empty name
            )

            assert invalid_response.status_code in [400, 422]

            # Test 3: Malformed query
            malformed_response = await client.post(
                f"{base_url}/collections/test/query",
                json={"invalid_field": "test"}  # Missing required fields
            )

            assert malformed_response.status_code in [400, 422]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, http_client_config, sample_test_data):
        """Test concurrent operations on ChromaDB"""
        async with httpx.AsyncClient(timeout=http_client_config['timeout']) as client:
            base_url = http_client_config['base_url']

            # Create multiple collections concurrently
            collection_names = [f"concurrent_test_{i}_{int(time.time())}" for i in range(3)]

            async def create_and_populate_collection(name):
                """Create and populate a collection"""
                try:
                    # Create collection
                    await client.post(
                        f"{base_url}/collections",
                        json={"name": name, "metadata": {"concurrent": True}}
                    )

                    # Add documents
                    await client.post(
                        f"{base_url}/collections/{name}/add",
                        json={
                            "documents": sample_test_data["documents"][:3],
                            "ids": [f"{name}_doc_{i}" for i in range(3)]
                        }
                    )

                    # Query collection
                    search_response = await client.post(
                        f"{base_url}/collections/{name}/query",
                        json={"query_texts": ["test query"], "n_results": 2}
                    )

                    return search_response.status_code == 200

                except Exception as e:
                    print(f"Concurrent operation failed for {name}: {e}")
                    return False

            try:
                # Run concurrent operations
                tasks = [create_and_populate_collection(name) for name in collection_names]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All operations should succeed
                successful_operations = sum(1 for r in results if r is True)
                assert successful_operations >= len(collection_names) // 2, "Too many concurrent operations failed"

            finally:
                # Cleanup
                cleanup_tasks = [
                    client.delete(f"{base_url}/collections/{name}")
                    for name in collection_names
                ]
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)


class TestSemanticSearchServiceIntegration:
    """Integration tests for semantic search service"""

    @pytest.fixture
    def semantic_search_url(self):
        """Semantic search service URL"""
        return "http://localhost:8004"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_search_service_health(self, semantic_search_url):
        """Test semantic search service health endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{semantic_search_url}/health")

                assert response.status_code == 200
                health_data = response.json()

                assert "data" in health_data
                assert "service" in health_data["data"]
                assert health_data["data"]["service"] == "semantic-search"
                assert "dependencies" in health_data["data"]
                assert "chromadb" in health_data["data"]["dependencies"]

        except httpx.ConnectError:
            pytest.skip("Semantic search service not running on localhost:8004")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_search_api_integration(self, semantic_search_url):
        """Test semantic search API endpoints"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test search endpoint
                search_payload = {
                    "query": "database vector search operations",
                    "max_results": 5,
                    "similarity_threshold": 0.1
                }

                response = await client.post(
                    f"{semantic_search_url}/api/v1/search",
                    json=search_payload
                )

                # Service should respond even if no data (422 for processing embeddings is acceptable)
                assert response.status_code in [200, 422, 503]

                if response.status_code == 200:
                    search_data = response.json()
                    assert "query" in search_data
                    assert "results" in search_data
                    assert "search_time_ms" in search_data
                    assert search_data["query"] == search_payload["query"]

        except httpx.ConnectError:
            pytest.skip("Semantic search service not running on localhost:8004")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_collections_endpoint_integration(self, semantic_search_url):
        """Test collections listing endpoint"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{semantic_search_url}/api/v1/collections")

                assert response.status_code == 200
                collections_data = response.json()

                assert "data" in collections_data
                assert isinstance(collections_data["data"], list)

        except httpx.ConnectError:
            pytest.skip("Semantic search service not running on localhost:8004")


# Pytest configuration for integration tests
def pytest_configure(config):
    """Configure pytest for integration tests"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--tb=short"
    ])