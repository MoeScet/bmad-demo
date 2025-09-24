"""
Pytest configuration for Story 1.5 Vector Database Infrastructure tests

Provides fixtures, markers, and configuration for comprehensive testing.
"""

import pytest
import asyncio
import os
import sys
import time
import uuid
from typing import Generator, Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests requiring live services"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers",
        "story_1_5: marks tests as Story 1.5 Vector Database Infrastructure tests"
    )
    config.addinivalue_line(
        "markers",
        "vector_database: marks tests as vector database specific tests"
    )
    config.addinivalue_line(
        "markers",
        "chromadb: marks tests as ChromaDB specific tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers"""
    for item in items:
        # Auto-mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Auto-mark performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def correlation_id() -> str:
    """Generate unique correlation ID for request tracing"""
    return str(uuid.uuid4())


@pytest.fixture
def test_timestamp() -> int:
    """Generate timestamp for unique test naming"""
    return int(time.time())


@pytest.fixture
def chromadb_config() -> Dict[str, Any]:
    """ChromaDB configuration for testing"""
    return {
        "host": os.getenv("CHROMADB_HOST", "localhost"),
        "port": int(os.getenv("CHROMADB_PORT", "8000")),
        "base_url": f"http://{os.getenv('CHROMADB_HOST', 'localhost')}:{os.getenv('CHROMADB_PORT', '8000')}/api/v1"
    }


@pytest.fixture
def semantic_search_config() -> Dict[str, Any]:
    """Semantic search service configuration"""
    return {
        "host": os.getenv("SEMANTIC_SEARCH_HOST", "localhost"),
        "port": int(os.getenv("SEMANTIC_SEARCH_PORT", "8004")),
        "base_url": f"http://{os.getenv('SEMANTIC_SEARCH_HOST', 'localhost')}:{os.getenv('SEMANTIC_SEARCH_PORT', '8004')}"
    }


@pytest.fixture
def sample_documents() -> list:
    """Sample documents for testing"""
    return [
        "ChromaDB is a vector database for building AI applications with embeddings",
        "FastAPI provides a modern, fast web framework for building APIs with Python",
        "Docker containers enable consistent application deployment across environments",
        "PostgreSQL offers robust relational database features for structured data",
        "Machine learning models can generate vector embeddings from text content",
        "Semantic search enables finding relevant documents based on meaning",
        "Vector similarity search uses mathematical distance calculations",
        "Railway platform provides simplified cloud deployment for applications",
        "Sentence transformers generate high-quality text embeddings for NLP",
        "Database indexing strategies improve query performance and scalability"
    ]


@pytest.fixture
def sample_search_queries() -> list:
    """Sample search queries for testing"""
    return [
        "vector database AI applications",
        "web framework API development",
        "container deployment infrastructure",
        "relational database management",
        "machine learning text embeddings",
        "semantic search document retrieval",
        "similarity search algorithms",
        "cloud deployment platforms",
        "NLP text processing models",
        "database performance optimization"
    ]


@pytest.fixture
def test_collection_metadata() -> Dict[str, Any]:
    """Standard metadata for test collections"""
    return {
        "test": True,
        "created_by": "pytest",
        "purpose": "story_1_5_testing",
        "framework": "pytest_asyncio"
    }


@pytest.fixture(scope="function")
def unique_collection_name(test_timestamp) -> str:
    """Generate unique collection name for each test"""
    return f"test_collection_{test_timestamp}_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def performance_test_data():
    """Large dataset for performance testing"""
    base_docs = [
        "Vector database performance optimization techniques and best practices",
        "Semantic search algorithms for large-scale document retrieval systems",
        "High-performance API design patterns with FastAPI and async programming",
        "Machine learning model deployment strategies for production environments",
        "Database indexing approaches for vector similarity search optimization",
        "Container orchestration patterns for AI and ML application deployment",
        "Distributed computing architectures for processing large ML workloads",
        "Real-time search engine design for high-throughput query processing",
        "Scalable vector embedding storage solutions for enterprise applications",
        "Performance monitoring and observability for database system management"
    ]

    # Generate larger dataset
    documents = []
    for i in range(50):  # 500 total documents
        for j, doc in enumerate(base_docs):
            documents.append(f"Document {i}-{j}: {doc}")

    return {
        "documents": documents,
        "metadatas": [
            {
                "doc_group": i // 10,
                "doc_index": i,
                "category": "performance_test",
                "subcategory": ["optimization", "algorithms", "design", "deployment", "indexing"][i % 5]
            }
            for i in range(len(documents))
        ]
    }


def pytest_runtest_setup(item):
    """Setup for each test"""
    # Skip integration tests if services aren't available (optional)
    if "integration" in item.keywords:
        # Could add service availability checks here
        pass


def pytest_runtest_teardown(item, nextitem):
    """Cleanup after each test"""
    # Could add cleanup logic here
    pass


# Custom assertions for vector database testing
class VectorDatabaseAssertions:
    """Custom assertions for vector database testing"""

    @staticmethod
    def assert_search_results_valid(results: Dict[str, Any], min_results: int = 1):
        """Assert search results have valid structure"""
        assert "documents" in results, "Search results missing documents"
        assert "distances" in results, "Search results missing distances"
        assert "ids" in results, "Search results missing ids"

        documents = results["documents"]
        distances = results["distances"]
        ids = results["ids"]

        if isinstance(documents[0], list):
            documents = documents[0]
            distances = distances[0]
            ids = ids[0]

        assert len(documents) >= min_results, f"Expected at least {min_results} results, got {len(documents)}"
        assert len(documents) == len(distances), "Documents and distances length mismatch"
        assert len(documents) == len(ids), "Documents and ids length mismatch"

        # Validate distance values
        for distance in distances:
            assert isinstance(distance, (int, float)), f"Distance should be numeric, got {type(distance)}"
            assert 0 <= distance <= 2.0, f"Distance {distance} outside expected range [0, 2]"

    @staticmethod
    def assert_performance_under_threshold(duration: float, threshold: float = 2.0):
        """Assert operation completed under performance threshold"""
        assert duration < threshold, f"Operation took {duration:.3f}s, exceeds {threshold}s threshold"

    @staticmethod
    def assert_collection_info_valid(info: Dict[str, Any], expected_name: str = None):
        """Assert collection info has valid structure"""
        assert "name" in info, "Collection info missing name"
        assert "count" in info, "Collection info missing count"

        if expected_name:
            assert info["name"] == expected_name, f"Collection name mismatch: {info['name']} != {expected_name}"

        assert isinstance(info["count"], int), f"Collection count should be int, got {type(info['count'])}"
        assert info["count"] >= 0, f"Collection count should be non-negative, got {info['count']}"


@pytest.fixture
def vector_assertions():
    """Provide vector database assertions"""
    return VectorDatabaseAssertions()


# Environment validation
def pytest_sessionstart(session):
    """Validate test environment at session start"""
    print("\n=== Story 1.5 Vector Database Infrastructure Test Suite ===")
    print("Validating test environment...")

    # Check Python path setup
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Project root: {project_root}")

    # Check required modules can be imported
    try:
        from shared.python.database.vector_client import ChromaDBClient
        print("✓ Vector client module available")
    except ImportError as e:
        print(f"✗ Vector client import failed: {e}")

    # Check if services are running (optional)
    import httpx
    import asyncio

    async def check_service(url: str, name: str):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✓ {name} service available at {url}")
                    return True
        except:
            pass
        print(f"ℹ {name} service not available at {url} (integration tests may be skipped)")
        return False

    # Check services
    async def check_services():
        await check_service("http://localhost:8000/api/v1/heartbeat", "ChromaDB")
        await check_service("http://localhost:8004/health", "Semantic Search")

    try:
        asyncio.run(check_services())
    except:
        pass

    print("Test environment validation complete.\n")


def pytest_sessionfinish(session, exitstatus):
    """Session cleanup"""
    print(f"\n=== Test Session Complete (exit status: {exitstatus}) ===")


# Pytest plugins
pytest_plugins = [
    "pytest_asyncio",
]