"""
Unit tests for PDF processing pipeline
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, mock_open
from pathlib import Path

from src.processing.pdf_processor import PDFProcessor, ProcessingJob
from src.config.settings import get_settings


class TestPDFProcessor:
    """Test suite for PDFProcessor class"""

    @pytest.fixture
    def processor(self):
        """Create PDFProcessor instance for testing"""
        return PDFProcessor()

    @pytest.fixture
    def mock_pdf_content(self):
        """Mock PDF content for testing"""
        return [
            ("This is page 1 content about troubleshooting washing machines. "
             "If your washer is not spinning, check the lid switch.", 1),
            ("Page 2 contains maintenance information. Clean the filter monthly "
             "to ensure optimal performance of your appliance.", 2),
            ("Safety information on page 3. Always unplug the unit before "
             "performing any maintenance or troubleshooting procedures.", 3)
        ]

    def test_processor_initialization(self, processor):
        """Test processor initializes correctly"""
        assert processor.settings is not None
        assert processor.text_cleaner is not None
        assert processor.content_manager is not None
        assert processor.quality_validator is not None
        assert processor.embedding_model is None  # Lazy loaded
        assert isinstance(processor.jobs, dict)

    def test_chunk_text_basic(self, processor):
        """Test basic text chunking functionality"""
        text = "This is a paragraph about washing machines.\n\nThis is another paragraph about maintenance."
        page_number = 1

        chunks = processor._chunk_text(text, page_number)

        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all('page_number' in chunk for chunk in chunks)
        assert all(chunk['page_number'] == page_number for chunk in chunks)

    def test_chunk_text_large_content(self, processor):
        """Test chunking of large text content"""
        # Create text larger than max chunk size
        large_text = "This is a test sentence. " * 100
        page_number = 1

        chunks = processor._chunk_text(large_text, page_number)

        assert len(chunks) > 1  # Should be split into multiple chunks
        for chunk in chunks:
            assert len(chunk['content']) <= processor.settings.MAX_CHUNK_SIZE + processor.settings.CHUNK_OVERLAP

    def test_chunk_text_empty_content(self, processor):
        """Test chunking with empty or minimal content"""
        empty_text = ""
        minimal_text = "Short"

        empty_chunks = processor._chunk_text(empty_text, 1)
        minimal_chunks = processor._chunk_text(minimal_text, 1)

        assert len(empty_chunks) == 0
        assert len(minimal_chunks) == 0  # Below minimum text length

    def test_extract_metadata_filename_patterns(self, processor):
        """Test metadata extraction from filename patterns"""
        test_cases = [
            ("whirlpool_manual.pdf", "Test content", "Whirlpool"),
            ("LG_WashingMachine_Guide.pdf", "Test content", "Lg"),
            ("samsung-user-manual.pdf", "Test content", "Samsung"),
            ("unknown_brand.pdf", "Test content", "Unknown")
        ]

        for filename, content, expected_manufacturer in test_cases:
            metadata = processor._extract_metadata(filename, content)
            assert metadata['manufacturer'] == expected_manufacturer
            assert 'model_series' in metadata
            assert 'content_type' in metadata
            assert metadata['source_manual'] == filename

    def test_extract_metadata_content_types(self, processor):
        """Test content type detection from text content"""
        test_cases = [
            ("troubleshooting guide", "troubleshooting"),
            ("maintenance schedule", "maintenance"),
            ("safety warnings", "safety"),
            ("warranty information", "warranty"),
            ("general information", "troubleshooting")  # default
        ]

        for content, expected_type in test_cases:
            metadata = processor._extract_metadata("test.pdf", content)
            assert metadata['content_type'] == expected_type

    @patch('src.processing.pdf_processor.PyPDF2.PdfReader')
    def test_extract_pdf_text_success(self, mock_pdf_reader, processor, mock_pdf_content):
        """Test successful PDF text extraction"""
        # Mock PDF reader
        mock_pages = []
        for content, page_num in mock_pdf_content:
            mock_page = Mock()
            mock_page.extract_text.return_value = content
            mock_pages.append(mock_page)

        mock_reader_instance = Mock()
        mock_reader_instance.pages = mock_pages
        mock_pdf_reader.return_value = mock_reader_instance

        # Mock file operations
        with patch('builtins.open', mock_open(read_data=b'fake pdf content')):
            result = processor._extract_pdf_text("test.pdf", "test-correlation-id")

        assert len(result) == 3
        assert result[0][0] == mock_pdf_content[0][0]
        assert result[0][1] == 1

    @patch('src.processing.pdf_processor.PyPDF2.PdfReader')
    def test_extract_pdf_text_empty_pages(self, mock_pdf_reader, processor):
        """Test PDF extraction with empty pages"""
        # Mock PDF with empty pages
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page, mock_page]
        mock_pdf_reader.return_value = mock_reader_instance

        with patch('builtins.open', mock_open(read_data=b'fake pdf content')):
            with pytest.raises(ValueError, match="No readable text found in PDF"):
                processor._extract_pdf_text("test.pdf", "test-correlation-id")

    @patch('src.processing.pdf_processor.PyPDF2.PdfReader')
    def test_extract_pdf_text_corrupted_file(self, mock_pdf_reader, processor):
        """Test PDF extraction with corrupted file"""
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")

        with patch('builtins.open', mock_open(read_data=b'fake pdf content')):
            with pytest.raises(Exception):
                processor._extract_pdf_text("test.pdf", "test-correlation-id")

    @pytest.mark.asyncio
    async def test_process_pdf_file_success(self, processor):
        """Test complete PDF processing pipeline success"""
        job_id = "test-job-123"
        correlation_id = "test-correlation"

        # Mock dependencies
        with patch.object(processor, '_extract_pdf_text') as mock_extract:
            with patch.object(processor, '_chunk_text') as mock_chunk:
                with patch.object(processor, '_load_embedding_model') as mock_model:
                    with patch.object(processor, '_extract_metadata') as mock_metadata:
                        with patch.object(processor.content_manager, 'store_content_chunk') as mock_store:
                            with patch.object(processor.quality_validator, 'calculate_readability_score') as mock_quality:
                                with patch.object(processor.quality_validator, 'check_for_duplicates') as mock_duplicates:

                                    # Setup mocks
                                    mock_extract.return_value = [("Test content", 1)]
                                    mock_chunk.return_value = [{"content": "Test content", "page_number": 1, "chunk_size": 100}]
                                    mock_model_instance = Mock()
                                    mock_model_instance.encode.return_value = [[0.1, 0.2, 0.3]]
                                    mock_model.return_value = mock_model_instance
                                    mock_metadata.return_value = {
                                        "manufacturer": "Test",
                                        "model_series": "Model",
                                        "content_type": "troubleshooting",
                                        "source_manual": "test.pdf"
                                    }
                                    mock_quality.return_value = 0.8
                                    mock_store.return_value = "content-id-123"
                                    mock_duplicates.return_value = []

                                    # Mock file cleanup
                                    with patch('pathlib.Path.unlink'):
                                        result = await processor.process_pdf_file("test.pdf", job_id, correlation_id)

                                    assert result is True
                                    assert job_id in processor.jobs
                                    job = processor.jobs[job_id]
                                    assert job.status == "completed"
                                    assert job.progress_percent == 100.0

    @pytest.mark.asyncio
    async def test_process_pdf_file_failure(self, processor):
        """Test PDF processing pipeline failure handling"""
        job_id = "test-job-fail"
        correlation_id = "test-correlation"

        # Mock failure in extraction
        with patch.object(processor, '_extract_pdf_text') as mock_extract:
            mock_extract.side_effect = Exception("Processing failed")

            result = await processor.process_pdf_file("test.pdf", job_id, correlation_id)

            assert result is False
            assert job_id in processor.jobs
            job = processor.jobs[job_id]
            assert job.status == "failed"
            assert job.error_details == "Processing failed"

    @pytest.mark.asyncio
    async def test_get_job_status_existing(self, processor):
        """Test getting status for existing job"""
        job_id = "test-job-status"
        job = ProcessingJob(job_id, "test.pdf")
        processor.jobs[job_id] = job

        status = await processor.get_job_status(job_id)

        assert status is not None
        assert status['job_id'] == job_id
        assert status['filename'] == "test.pdf"
        assert status['status'] == "queued"

    @pytest.mark.asyncio
    async def test_get_job_status_nonexistent(self, processor):
        """Test getting status for non-existent job"""
        status = await processor.get_job_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_list_all_jobs(self, processor):
        """Test listing all jobs"""
        # Add test jobs
        job1 = ProcessingJob("job1", "file1.pdf")
        job2 = ProcessingJob("job2", "file2.pdf")
        processor.jobs["job1"] = job1
        processor.jobs["job2"] = job2

        jobs = await processor.list_all_jobs()

        assert len(jobs) == 2
        job_ids = [job['job_id'] for job in jobs if job]
        assert "job1" in job_ids
        assert "job2" in job_ids

    @pytest.mark.asyncio
    async def test_delete_job_success(self, processor):
        """Test successful job deletion"""
        job_id = "test-delete"
        processor.jobs[job_id] = ProcessingJob(job_id, "test.pdf")

        result = await processor.delete_job(job_id)

        assert result is True
        assert job_id not in processor.jobs

    @pytest.mark.asyncio
    async def test_delete_job_nonexistent(self, processor):
        """Test deleting non-existent job"""
        result = await processor.delete_job("nonexistent")
        assert result is False

    def test_processing_job_initialization(self):
        """Test ProcessingJob initialization"""
        job_id = "test-job"
        filename = "test.pdf"

        job = ProcessingJob(job_id, filename)

        assert job.job_id == job_id
        assert job.filename == filename
        assert job.status == "queued"
        assert job.progress_percent == 0.0
        assert job.message == "Job queued for processing"
        assert job.created_at is not None
        assert job.completed_at is None
        assert job.error_details is None

    @pytest.mark.asyncio
    async def test_load_embedding_model_lazy_loading(self, processor):
        """Test lazy loading of embedding model"""
        assert processor.embedding_model is None

        with patch('src.processing.pdf_processor.SentenceTransformer') as mock_transformer:
            mock_instance = Mock()
            mock_transformer.return_value = mock_instance

            model = await processor._load_embedding_model()

            assert model == mock_instance
            assert processor.embedding_model == mock_instance
            mock_transformer.assert_called_once_with(processor.settings.EMBEDDING_MODEL)

    @pytest.mark.asyncio
    async def test_load_embedding_model_reuse(self, processor):
        """Test that embedding model is reused after first load"""
        mock_model = Mock()
        processor.embedding_model = mock_model

        model = await processor._load_embedding_model()

        assert model == mock_model  # Same instance returned


if __name__ == "__main__":
    pytest.main([__file__])