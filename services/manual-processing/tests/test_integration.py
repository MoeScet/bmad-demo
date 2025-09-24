"""
Integration tests for Manual Processing Service
"""

import pytest
import asyncio
import uuid
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
import json

# Import FastAPI app
from src.main import app


class TestManualProcessingIntegration:
    """Integration tests for the complete manual processing pipeline"""

    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_database(self):
        """Mock database connections"""
        with patch('src.api.health.get_db_session') as mock_db:
            # Mock successful database connection
            mock_session = AsyncMock()
            mock_session.execute.return_value = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            yield mock_db

    @pytest.fixture
    def mock_chromadb(self):
        """Mock ChromaDB HTTP responses"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"nanosecond heartbeat": 123456789}

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            yield mock_client

    @pytest.mark.asyncio
    async def test_health_check_success(self, client, mock_database, mock_chromadb):
        """Test successful health check"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "service" in data["data"]
        assert "checks" in data["data"]

    @pytest.mark.asyncio
    async def test_health_check_database_failure(self, client, mock_chromadb):
        """Test health check with database failure"""
        with patch('src.api.health.get_db_session') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "degraded"
            assert data["data"]["checks"]["database"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_chromadb_failure(self, client, mock_database):
        """Test health check with ChromaDB failure"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("ChromaDB down")

            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "degraded"
            assert data["data"]["checks"]["chromadb"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["service"] == "BMAD Manual Processing Service"
        assert "version" in data["data"]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        # Create a fake text file
        files = {"file": ("test.txt", b"fake text content", "text/plain")}

        response = await client.post("/api/v1/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Only PDF files are supported" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client):
        """Test upload with file too large"""
        # Create a fake PDF that's too large (mock 60MB content)
        large_content = b"fake pdf content" * (1024 * 1024 * 4)  # ~60MB
        files = {"file": ("large.pdf", large_content, "application/pdf")}

        response = await client.post("/api/v1/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "exceeds" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client):
        """Test upload with empty file"""
        files = {"file": ("empty.pdf", b"", "application/pdf")}

        response = await client.post("/api/v1/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "empty or corrupted" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_upload_success(self, client):
        """Test successful file upload"""
        # Mock the background processing
        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.process_pdf_file = AsyncMock()

            # Create a valid PDF file
            pdf_content = b"fake pdf content that is valid"
            files = {"file": ("test_manual.pdf", pdf_content, "application/pdf")}

            response = await client.post("/api/v1/upload", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert "job_id" in data["data"]
            assert data["data"]["filename"] == "test_manual.pdf"
            assert data["data"]["status"] == "queued"

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, client):
        """Test getting status for non-existent job"""
        job_id = str(uuid.uuid4())

        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.get_job_status.return_value = None

            response = await client.get(f"/api/v1/status/{job_id}")

            assert response.status_code == 404
            data = response.json()
            assert "Job not found" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, client):
        """Test getting status for existing job"""
        job_id = str(uuid.uuid4())

        mock_status = {
            "job_id": job_id,
            "status": "processing",
            "filename": "test.pdf",
            "progress_percent": 50.0,
            "message": "Processing content",
            "created_at": "2023-01-01T00:00:00Z"
        }

        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.get_job_status.return_value = mock_status

            response = await client.get(f"/api/v1/status/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["job_id"] == job_id
            assert data["data"]["status"] == "processing"

    @pytest.mark.asyncio
    async def test_list_processing_jobs(self, client):
        """Test listing all processing jobs"""
        mock_jobs = [
            {
                "job_id": "job1",
                "status": "completed",
                "filename": "manual1.pdf",
                "progress_percent": 100.0,
                "message": "Completed",
                "created_at": "2023-01-01T00:00:00Z"
            },
            {
                "job_id": "job2",
                "status": "processing",
                "filename": "manual2.pdf",
                "progress_percent": 75.0,
                "message": "Processing",
                "created_at": "2023-01-01T01:00:00Z"
            }
        ]

        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.list_all_jobs.return_value = mock_jobs

            response = await client.get("/api/v1/jobs")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert len(data["data"]["jobs"]) == 2
            assert data["data"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_delete_job_success(self, client):
        """Test successful job deletion"""
        job_id = str(uuid.uuid4())

        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.delete_job.return_value = True

            response = await client.delete(f"/api/v1/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, client):
        """Test deleting non-existent job"""
        job_id = str(uuid.uuid4())

        with patch('src.api.upload.PDFProcessor') as mock_processor:
            mock_processor.return_value.delete_job.return_value = False

            response = await client.delete(f"/api/v1/jobs/{job_id}")

            assert response.status_code == 404
            data = response.json()
            assert "Job not found" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_content_search_success(self, client):
        """Test successful content search"""
        search_request = {
            "query": "troubleshooting washing machine",
            "max_results": 10
        }

        mock_results = {
            "query": "troubleshooting washing machine",
            "results": [
                {
                    "id": str(uuid.uuid4()),
                    "manufacturer": "Whirlpool",
                    "section_title": "Troubleshooting Guide",
                    "content": "If your washing machine won't start...",
                    "similarity_score": 0.95
                }
            ],
            "total_results": 1,
            "search_time_ms": 150.0
        }

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.search_content.return_value = mock_results

            response = await client.post("/api/v1/content/search", json=search_request)

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["total_results"] == 1
            assert data["data"]["query"] == search_request["query"]

    @pytest.mark.asyncio
    async def test_content_search_no_results(self, client):
        """Test content search with no results"""
        search_request = {
            "query": "nonexistent topic",
            "max_results": 10
        }

        mock_results = {
            "query": "nonexistent topic",
            "results": [],
            "total_results": 0,
            "search_time_ms": 50.0
        }

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.search_content.return_value = mock_results

            response = await client.post("/api/v1/content/search", json=search_request)

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["total_results"] == 0

    @pytest.mark.asyncio
    async def test_list_content_with_filters(self, client):
        """Test listing content with filters"""
        mock_content = [
            {
                "id": str(uuid.uuid4()),
                "manufacturer": "LG",
                "model_series": "WM3900H",
                "section_title": "Maintenance Guide",
                "content": "Regular maintenance...",
                "content_type": "maintenance",
                "confidence_score": 0.85,
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.list_content.return_value = mock_content

            response = await client.get(
                "/api/v1/content?manufacturer=LG&content_type=maintenance&limit=10"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert len(data["data"]["content"]) == 1
            assert data["data"]["content"][0]["manufacturer"] == "LG"

    @pytest.mark.asyncio
    async def test_get_content_by_id_success(self, client):
        """Test getting specific content by ID"""
        content_id = str(uuid.uuid4())
        mock_content = {
            "id": content_id,
            "manufacturer": "Samsung",
            "section_title": "Troubleshooting",
            "content": "Complete troubleshooting content...",
            "content_type": "troubleshooting"
        }

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.get_content_by_id.return_value = mock_content

            response = await client.get(f"/api/v1/content/{content_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["id"] == content_id

    @pytest.mark.asyncio
    async def test_get_content_by_id_not_found(self, client):
        """Test getting non-existent content"""
        content_id = str(uuid.uuid4())

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.get_content_by_id.return_value = None

            response = await client.get(f"/api/v1/content/{content_id}")

            assert response.status_code == 404
            data = response.json()
            assert "Content not found" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_delete_content_success(self, client):
        """Test successful content deletion"""
        content_id = str(uuid.uuid4())

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.delete_content.return_value = True

            response = await client.delete(f"/api/v1/content/{content_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["content_id"] == content_id

    @pytest.mark.asyncio
    async def test_reprocess_content_success(self, client):
        """Test successful content reprocessing"""
        content_id = str(uuid.uuid4())

        with patch('src.api.processing.ContentManager') as mock_manager:
            mock_manager.return_value.reprocess_content.return_value = True

            response = await client.post(f"/api/v1/content/{content_id}/reprocess")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert "reprocessing initiated" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_quality_report(self, client):
        """Test quality report generation"""
        mock_report = {
            "generated_at": "2023-01-01T00:00:00Z",
            "total_content_items": 100,
            "content_type_distribution": {
                "troubleshooting": 50,
                "maintenance": 30,
                "safety": 20
            },
            "quality_metrics": {
                "average_quality_score": 0.85,
                "low_quality_items": 5
            },
            "health_status": "healthy"
        }

        with patch('src.api.processing.QualityValidator') as mock_validator:
            mock_validator.return_value.generate_quality_report.return_value = mock_report

            response = await client.get("/api/v1/quality/report")

            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["total_content_items"] == 100
            assert data["data"]["health_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_correlation_id_propagation(self, client):
        """Test that correlation IDs are properly propagated"""
        correlation_id = str(uuid.uuid4())

        response = await client.get("/health", headers={"x-correlation-id": correlation_id})

        assert response.status_code == 200
        assert response.headers.get("x-correlation-id") == correlation_id

    @pytest.mark.asyncio
    async def test_global_exception_handler(self, client):
        """Test global exception handling"""
        with patch('src.api.health.get_db_session') as mock_db:
            # Force an unhandled exception
            mock_db.side_effect = RuntimeError("Unexpected error")

            response = await client.get("/health")

            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["error"]["message"]
            assert "correlation_id" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__])