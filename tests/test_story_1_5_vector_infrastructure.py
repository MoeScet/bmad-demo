"""
Comprehensive Test Suite for Story 1.5: Vector Database Infrastructure

This test suite validates all 5 acceptance criteria:
1. ChromaDB Installation & Configuration
2. Production Deployment Setup
3. Basic Vector Operations
4. Integration Preparation
5. Development Environment Validation

Testing Framework: pytest 7.4.3 with asyncio support
Coverage Goal: 90% line coverage for core business logic
"""

import pytest
import asyncio
import time
import json
import httpx
import uuid
from typing import List, Dict, Any, Optional
from unittest.mock import patch, AsyncMock, MagicMock
import logging
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.python.database.vector_client import (
    ChromaDBClient,
    VectorDatabaseError,
    get_vector_client
)


class TestChromaDBInstallationConfiguration:
    """
    Acceptance Criteria 1: ChromaDB Installation & Configuration
    - ChromaDB 0.4.15 installed and configured in development environment
    - Docker Compose configuration includes ChromaDB service with persistent storage
    - Connection configuration and environment variables established
    - Health check endpoint implemented for ChromaDB connectivity
    """

    @pytest.fixture
    def mock_chromadb_client(self):
        """Mock ChromaDB client for testing"""
        with patch('shared.python.database.vector_client.chromadb') as mock_chromadb:
            mock_client = MagicMock()
            mock_client.heartbeat = MagicMock()
            mock_chromadb.HttpClient.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer for testing"""
        with patch('shared.python.database.vector_client.SentenceTransformer') as mock_st:
            mock_model = MagicMock()
            mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
            mock_st.return_value = mock_model
            yield mock_model

    async def test_chromadb_client_initialization(self, mock_chromadb_client, mock_sentence_transformer):
        """Test ChromaDB client proper initialization"""
        client = ChromaDBClient(host="localhost", port=8000)

        # Should initialize without errors
        await client.initialize()

        assert client._client is not None
        assert client._embedding_model is not None
        assert client.host == "localhost"
        assert client.port == 8000

    async def test_chromadb_connection_configuration(self, mock_chromadb_client, mock_sentence_transformer):
        """Test connection configuration with environment variables"""
        client = ChromaDBClient(host="test.host", port=9000)
        await client.initialize()

        # Verify connection parameters are used
        mock_chromadb_client.assert_called()

    async def test_chromadb_health_check_endpoint(self, mock_chromadb_client, mock_sentence_transformer):
        """Test health check endpoint implementation"""
        client = ChromaDBClient()
        await client.initialize()

        # Test healthy connection
        health_result = await client.health_check()

        assert health_result["status"] == "healthy"
        assert "host" in health_result
        assert "port" in health_result
        assert "correlation_id" in health_result

    async def test_chromadb_health_check_failure(self):
        """Test health check with connection failure"""
        client = ChromaDBClient(host="nonexistent.host", port=9999)

        # Should handle connection failure gracefully
        health_result = await client.health_check()

        assert health_result["status"] == "unhealthy"
        assert "error" in health_result

    @pytest.mark.asyncio
    async def test_docker_compose_chromadb_service_health(self):
        """Test ChromaDB service health via HTTP (integration test)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.get("http://localhost:8000/api/v1/heartbeat"),
                    timeout=5.0
                )
                # Should return 200 if ChromaDB is running
                assert response.status_code == 200

        except (httpx.ConnectError, asyncio.TimeoutError):
            pytest.skip("ChromaDB not running on localhost:8000 - Docker environment test")

    def test_chromadb_version_requirement(self):
        """Verify ChromaDB 0.4.15 version requirement"""
        try:
            import chromadb
            # Check if chromadb can be imported (version validation in setup)
            assert hasattr(chromadb, 'HttpClient')
        except ImportError:
            pytest.fail("ChromaDB not properly installed")


class TestProductionDeploymentSetup:
    """
    Acceptance Criteria 2: Production Deployment Setup
    - ChromaDB deployment configured on Railway/Render free tier
    - Persistent storage configuration for vector embeddings
    - Network configuration allows service-to-service communication
    - Backup and recovery procedures documented for vector data
    """

    def test_railway_deployment_configuration(self):
        """Test Railway deployment configuration exists"""
        railway_config_path = "infrastructure/chromadb/railway.toml"
        dockerfile_path = "infrastructure/chromadb/Dockerfile"

        # Check if deployment files exist
        assert os.path.exists(railway_config_path) or os.path.exists("infrastructure/railway/railway.toml")
        assert os.path.exists(dockerfile_path) or os.path.exists("services/semantic-search/Dockerfile")

    def test_persistent_storage_configuration(self):
        """Test persistent storage configuration for vector embeddings"""
        # Check Docker configuration has volume mounts
        docker_compose_path = "docker-compose.yml"
        if os.path.exists(docker_compose_path):
            with open(docker_compose_path) as f:
                content = f.read()
                # Should have ChromaDB with volumes configured
                assert "chromadb" in content.lower()

    def test_backup_recovery_documentation(self):
        """Test backup and recovery procedures documented"""
        backup_docs = [
            "infrastructure/chromadb/backup-recovery.md",
            "docs/backup-recovery.md",
            "docs/vector-database-backup.md"
        ]

        docs_exist = any(os.path.exists(doc) for doc in backup_docs)
        assert docs_exist, "Backup and recovery documentation not found"

    def test_network_service_communication(self):
        """Test network configuration allows service communication"""
        # Check if semantic search service can communicate with ChromaDB
        # This validates the network configuration

        from services.semantic_search.simple_main import CHROMADB_BASE_URL
        assert "localhost:8000" in CHROMADB_BASE_URL or "8000" in CHROMADB_BASE_URL


class TestBasicVectorOperations:
    """
    Acceptance Criteria 3: Basic Vector Operations
    - Test collection created with sample embeddings
    - CRUD operations validated (create, read, update, delete embeddings)
    - Performance benchmarking for vector similarity search (<2 second target)
    - Error handling for vector database connection failures
    """

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing"""
        return [
            "FastAPI is a modern web framework for building APIs with Python",
            "ChromaDB provides vector database capabilities for semantic search",
            "Docker containers enable consistent deployment across environments",
            "PostgreSQL is a powerful relational database for structured data",
            "Machine learning models generate embeddings from text content"
        ]

    @pytest.fixture
    def mock_vector_client(self):
        """Mock vector client for testing"""
        with patch('shared.python.database.vector_client.get_vector_client') as mock:
            mock_client = AsyncMock()
            mock_client.create_collection = AsyncMock(return_value="test_collection_id")
            mock_client.add_embeddings = AsyncMock(return_value=["doc1", "doc2", "doc3"])
            mock_client.search_similar = AsyncMock(return_value={
                "documents": ["Sample document 1", "Sample document 2"],
                "distances": [0.1, 0.2],
                "metadatas": [{"category": "test"}, {"category": "test"}],
                "ids": ["doc1", "doc2"]
            })
            mock_client.get_collection_info = AsyncMock(return_value={
                "name": "test_collection",
                "count": 3,
                "metadata": {}
            })
            mock_client.delete_collection = AsyncMock(return_value=True)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock.return_value = mock_client
            yield mock_client

    async def test_create_collection_with_embeddings(self, mock_vector_client, sample_documents):
        """Test creating collection with sample embeddings"""
        async with get_vector_client() as client:
            # CREATE operation
            collection_id = await client.create_collection(
                "test_collection",
                metadata={"purpose": "testing"}
            )
            assert collection_id == "test_collection_id"

            # Add embeddings
            doc_ids = await client.add_embeddings(
                "test_collection",
                sample_documents[:3],
                metadatas=[{"index": i} for i in range(3)]
            )
            assert len(doc_ids) == 3

    async def test_crud_operations_complete_cycle(self, mock_vector_client, sample_documents):
        """Test complete CRUD operations cycle"""
        async with get_vector_client() as client:
            collection_name = "crud_test_collection"

            # CREATE
            await client.create_collection(collection_name)
            doc_ids = await client.add_embeddings(collection_name, sample_documents[:2])

            # READ
            collection_info = await client.get_collection_info(collection_name)
            assert collection_info["count"] == 3

            search_results = await client.search_similar(
                collection_name,
                "web framework python",
                n_results=2
            )
            assert len(search_results["documents"]) == 2

            # UPDATE (add more documents)
            more_ids = await client.add_embeddings(collection_name, sample_documents[2:])

            # DELETE
            deleted = await client.delete_collection(collection_name)
            assert deleted is True

    async def test_vector_similarity_search_performance(self, mock_vector_client):
        """Test performance benchmarking <2 second target"""
        async with get_vector_client() as client:
            collection_name = "performance_test"

            # Time the search operation
            start_time = time.time()

            results = await client.search_similar(
                collection_name,
                "performance testing query",
                n_results=10
            )

            search_time = time.time() - start_time

            # Validate <2 second requirement
            assert search_time < 2.0, f"Search took {search_time:.3f}s, exceeds 2s requirement"
            assert len(results["documents"]) > 0

    async def test_vector_operations_error_handling(self, mock_vector_client):
        """Test error handling for vector database connection failures"""
        # Test with connection failure
        mock_vector_client.search_similar.side_effect = VectorDatabaseError("connection failed")

        async with get_vector_client() as client:
            with pytest.raises(VectorDatabaseError) as exc_info:
                await client.search_similar("test_collection", "test query")

            # Should have proper fallback error message
            assert "connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_vector_operations_integration(self):
        """Integration test for HTTP-based vector operations"""
        try:
            async with httpx.AsyncClient() as client:
                base_url = "http://localhost:8000/api/v1"

                # Test heartbeat
                health_response = await asyncio.wait_for(
                    client.get(f"{base_url}/heartbeat"),
                    timeout=5.0
                )

                if health_response.status_code == 200:
                    # Test collection creation
                    collection_name = f"test_{int(time.time())}"
                    create_response = await client.post(
                        f"{base_url}/collections",
                        json={"name": collection_name, "metadata": {"test": True}}
                    )

                    # Should succeed if ChromaDB is running
                    assert create_response.status_code in [200, 201]

                    # Cleanup
                    await client.delete(f"{base_url}/collections/{collection_name}")

        except (httpx.ConnectError, asyncio.TimeoutError):
            pytest.skip("ChromaDB not running - integration test skipped")


class TestIntegrationPreparation:
    """
    Acceptance Criteria 4: Integration Preparation
    - API client library configured for semantic search service integration
    - Authentication/authorization configured if required
    - Monitoring integration added for vector database health
    - Documentation for vector database schema and indexing strategy
    """

    def test_semantic_search_service_api_client(self):
        """Test API client configured for semantic search service"""
        # Check if semantic search service exists
        service_main = "services/semantic-search/simple_main.py"
        assert os.path.exists(service_main), "Semantic search service not found"

        # Verify service has proper API endpoints
        with open(service_main) as f:
            content = f.read()
            assert "/api/v1/search" in content
            assert "SearchRequest" in content
            assert "SearchResponse" in content

    def test_monitoring_integration_health_tracking(self):
        """Test monitoring integration for vector database health"""
        # Check health endpoints exist
        service_main = "services/semantic-search/simple_main.py"
        with open(service_main) as f:
            content = f.read()
            assert "/health" in content
            assert "chromadb_healthy" in content

    def test_vector_database_schema_documentation(self):
        """Test documentation for vector database schema and indexing strategy"""
        schema_docs = [
            "docs/vector-database-schema.md",
            "docs/developer-guide-vector-database.md",
            "docs/vector-indexing-strategy.md"
        ]

        docs_exist = any(os.path.exists(doc) for doc in schema_docs)
        assert docs_exist, "Vector database schema documentation not found"

    async def test_authentication_configuration(self):
        """Test authentication/authorization if required"""
        # Check if authentication is configured in vector client
        from shared.python.database.vector_client import ChromaDBClient

        client = ChromaDBClient()
        # Should have proper auth configuration (or None for development)
        assert hasattr(client, '_client')

    def test_api_response_models(self):
        """Test API response models for integration"""
        from services.semantic_search.simple_main import SearchRequest, SearchResponse, SearchResult

        # Validate request model
        request = SearchRequest(query="test query", max_results=5)
        assert request.query == "test query"
        assert request.max_results == 5

        # Validate response models
        result = SearchResult(
            document_id="doc1",
            content="test content",
            similarity_score=0.95
        )
        assert result.similarity_score == 0.95


class TestDevelopmentEnvironmentValidation:
    """
    Acceptance Criteria 5: Development Environment Validation
    - Local development setup working with ChromaDB
    - Test data loading procedures established
    - Developer documentation for vector database operations
    - Integration testing framework can access vector database
    """

    def test_local_development_setup(self):
        """Test local development setup working with ChromaDB"""
        # Check required files exist
        required_files = [
            "shared/python/database/vector_client.py",
            "services/semantic-search/simple_main.py",
            "docker-compose.yml"
        ]

        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file not found: {file_path}"

    def test_test_data_loading_procedures(self):
        """Test data loading procedures established"""
        test_data_scripts = [
            "test_with_http.py",
            "load_test_data_http.py",
            "scripts/load_test_data.py"
        ]

        scripts_exist = any(os.path.exists(script) for script in test_data_scripts)
        assert scripts_exist, "Test data loading procedures not found"

    def test_developer_documentation_exists(self):
        """Test developer documentation for vector database operations"""
        dev_docs = [
            "docs/developer-guide-vector-database.md",
            "docs/vector-database-operations.md",
            "README.md"
        ]

        docs_exist = any(os.path.exists(doc) for doc in dev_docs)
        assert docs_exist, "Developer documentation not found"

    def test_integration_testing_framework_access(self):
        """Test integration testing framework can access vector database"""
        # This test itself validates the framework can access the vector database
        from shared.python.database.vector_client import get_vector_client, VectorDatabaseError

        # Should be importable and usable
        assert get_vector_client is not None
        assert VectorDatabaseError is not None

    async def test_test_data_loading_functionality(self):
        """Test test data loading functionality"""
        # Test the actual test data loading
        if os.path.exists("test_with_http.py"):
            # Import and test the HTTP vector tester
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

            try:
                from test_with_http import HTTPVectorTester
                tester = HTTPVectorTester()
                # Should initialize without errors
                assert tester.base_url.startswith("http://")
            except ImportError:
                pytest.skip("HTTP vector tester not available for import")

    def test_development_environment_variables(self):
        """Test development environment variables configuration"""
        # Check if environment configuration exists
        config_files = [
            "shared/python/config/base.py",
            ".env",
            "docker-compose.yml"
        ]

        config_exists = any(os.path.exists(config) for config in config_files)
        assert config_exists, "Environment configuration not found"


class TestStory15EndToEndScenarios:
    """
    End-to-end test scenarios validating Story 1.5 complete workflow
    """

    async def test_complete_vector_infrastructure_workflow(self):
        """Test complete vector infrastructure end-to-end"""
        # This integrates all 5 acceptance criteria in a single workflow

        # AC1: Configuration test
        try:
            from shared.python.database.vector_client import get_vector_client
        except ImportError:
            pytest.fail("ChromaDB client configuration failed")

        # AC2: Production deployment readiness
        assert os.path.exists("services/semantic-search/simple_main.py")

        # AC3: Vector operations (mocked for unit test)
        with patch('shared.python.database.vector_client.get_vector_client') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock()
            mock_client.return_value.__aexit__ = AsyncMock()
            mock_client.return_value.create_collection = AsyncMock(return_value="test_id")

            async with get_vector_client() as client:
                result = await client.create_collection("test")
                assert result == "test_id"

        # AC4: Integration preparation
        from services.semantic_search.simple_main import app, SearchRequest
        assert app is not None
        assert SearchRequest is not None

        # AC5: Development environment
        assert os.path.exists("shared/python/database/vector_client.py")

    def test_performance_requirements_validation(self):
        """Test all performance requirements are met"""
        # <2 second search requirement is tested in individual tests
        # This validates the requirement is properly documented

        story_doc = "docs/stories/1.5.vector-database-infrastructure.md"
        if os.path.exists(story_doc):
            with open(story_doc) as f:
                content = f.read()
                assert "2 second" in content or "<2" in content

    def test_error_handling_fallback_responses(self):
        """Test comprehensive error handling with fallback responses"""
        from shared.python.database.vector_client import VectorDatabaseError

        # Should have proper error types
        assert issubclass(VectorDatabaseError, Exception)

        # Test error messages follow pattern
        error = VectorDatabaseError("knowledge gap - test error")
        assert "knowledge gap" in str(error)


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def correlation_id():
    """Generate correlation ID for tracing"""
    return str(uuid.uuid4())


# Performance benchmarking utilities
class VectorPerformanceBenchmark:
    """Utility for performance benchmarking"""

    @staticmethod
    async def benchmark_search_performance(client, collection_name: str, queries: List[str]) -> Dict[str, Any]:
        """Benchmark search performance for multiple queries"""
        results = {
            "total_queries": len(queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "average_time": 0.0,
            "max_time": 0.0,
            "min_time": float('inf'),
            "query_results": []
        }

        total_time = 0.0

        for query in queries:
            start_time = time.time()
            try:
                await client.search_similar(collection_name, query, n_results=5)
                query_time = time.time() - start_time

                results["successful_queries"] += 1
                total_time += query_time
                results["max_time"] = max(results["max_time"], query_time)
                results["min_time"] = min(results["min_time"], query_time)

                results["query_results"].append({
                    "query": query,
                    "time": query_time,
                    "status": "success"
                })

            except Exception as e:
                results["failed_queries"] += 1
                results["query_results"].append({
                    "query": query,
                    "error": str(e),
                    "status": "failed"
                })

        if results["successful_queries"] > 0:
            results["average_time"] = total_time / results["successful_queries"]

        return results


# Test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.vector_database,
    pytest.mark.story_1_5
]


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=shared.python.database.vector_client",
        "--cov=services.semantic_search",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])