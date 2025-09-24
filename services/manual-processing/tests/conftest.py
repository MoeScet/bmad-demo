"""
Pytest configuration and shared fixtures for manual processing tests
"""

import pytest
import asyncio
import tempfile
import uuid
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test configuration settings"""
    return Settings(
        ENVIRONMENT="test",
        DATABASE_URL="sqlite+aiosqlite:///test.db",
        CHROMADB_HOST="localhost",
        CHROMADB_PORT=8000,
        MAX_FILE_SIZE_MB=10,
        UPLOAD_DIRECTORY=tempfile.mkdtemp(),
        PROCESSING_TIMEOUT_SECONDS=30,
        EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
        MIN_READABILITY_SCORE=0.3,
        DUPLICATE_SIMILARITY_THRESHOLD=0.9
    )


@pytest.fixture
def mock_correlation_id():
    """Generate test correlation ID"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_pdf_content():
    """Sample PDF text content for testing"""
    return [
        ("Chapter 1: Troubleshooting\n\nIf your washing machine is not working properly, "
         "follow these troubleshooting steps. First, check that the power cord is properly "
         "connected to the outlet.", 1),
        ("Chapter 2: Maintenance\n\nRegular maintenance is essential for optimal performance. "
         "Clean the lint filter after every use. Check the water inlet hoses monthly for "
         "signs of wear or damage.", 2),
        ("Chapter 3: Safety\n\nAlways disconnect the power before performing any maintenance. "
         "Never operate the machine with the door open. Keep children away from the appliance "
         "during operation.", 3)
    ]


@pytest.fixture
def sample_manual_content():
    """Sample manual content items for testing"""
    return [
        {
            "id": str(uuid.uuid4()),
            "manufacturer": "Whirlpool",
            "model_series": "WTW5000DW",
            "section_title": "Troubleshooting Guide",
            "content": "If the washer will not start, check the following items...",
            "content_type": "troubleshooting",
            "confidence_score": 0.85,
            "source_manual": "whirlpool_manual.pdf",
            "page_reference": "page_12",
            "created_at": "2023-01-01T00:00:00Z"
        },
        {
            "id": str(uuid.uuid4()),
            "manufacturer": "LG",
            "model_series": "WM3900HWA",
            "section_title": "Maintenance Schedule",
            "content": "Monthly maintenance tasks include cleaning the detergent dispenser...",
            "content_type": "maintenance",
            "confidence_score": 0.92,
            "source_manual": "lg_manual.pdf",
            "page_reference": "page_25",
            "created_at": "2023-01-01T00:00:00Z"
        }
    ]


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model"""
    mock_model = Mock()
    mock_model.encode.return_value = [
        [0.1, 0.2, 0.3, 0.4, 0.5],  # Mock embedding vector
        [0.6, 0.7, 0.8, 0.9, 1.0]   # Another mock embedding
    ]
    return mock_model


@pytest.fixture
def mock_chromadb_response():
    """Mock ChromaDB HTTP API response"""
    return {
        "documents": [["Sample document content", "Another document"]],
        "distances": [[0.1, 0.3]],
        "metadatas": [[{"manufacturer": "Whirlpool"}, {"manufacturer": "LG"}]],
        "ids": [["doc1", "doc2"]]
    }


@pytest.fixture
def mock_database_session():
    """Mock database session for testing"""
    session = AsyncMock()
    session.execute.return_value = AsyncMock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def sample_processing_job():
    """Sample processing job for testing"""
    from src.processing.pdf_processor import ProcessingJob
    return ProcessingJob("test-job-123", "test_manual.pdf")


@pytest.fixture
def temp_pdf_file():
    """Create temporary PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"fake pdf content for testing")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def quality_test_texts():
    """Sample texts for quality validation testing"""
    return {
        "high_quality": (
            "This is a well-structured paragraph about washing machine maintenance. "
            "Regular cleaning of the detergent dispenser prevents buildup and ensures "
            "optimal performance. Follow these steps for proper maintenance procedures."
        ),
        "medium_quality": (
            "Washing machine troubleshooting steps include checking power connection "
            "and water supply. Some common issues can be resolved easily."
        ),
        "low_quality": (
            "a b c d e f g h i j k l m n o p q r s t u v w x y z 123 456 789 !@# $%^"
        ),
        "ocr_artifacts": (
            "Th1s t3xt h@s m@ny OCR @rt1f@cts @nd sp3c1@l ch@r@ct3rs th@t m@k3 1t h@rd t0 r3@d"
        )
    }


class MockAsyncContextManager:
    """Mock async context manager for testing"""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for testing"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}

    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.delete.return_value = mock_response

    return MockAsyncContextManager(mock_client)


# Pytest markers
pytest_plugins = ["pytest_asyncio"]

# Test configuration
pytest.mark.asyncio.scope = "function"