# Manual Processing Service

A FastAPI-based service for processing PDF manuals and generating vector embeddings for semantic search in the BMAD troubleshooting system.

## Features

- **PDF Processing**: Extract text from PDF manuals using PyPDF2
- **Text Cleaning**: Normalize and clean extracted text for better quality
- **Vector Embeddings**: Generate embeddings using sentence-transformers
- **Content Storage**: Store processed content in PostgreSQL and ChromaDB
- **Quality Assurance**: Validate content quality and detect duplicates
- **Admin Interface**: React components for upload and content management
- **Background Processing**: Async processing with job status tracking

## Architecture

### Core Components

- **PDFProcessor**: Main processing pipeline for PDF files
- **TextCleaner**: Text normalization and quality validation
- **ContentManager**: Database operations for manual content
- **QualityValidator**: Content quality assessment and reporting

### API Endpoints

- `POST /api/v1/upload` - Upload PDF files for processing
- `GET /api/v1/status/{job_id}` - Get processing job status
- `GET /api/v1/jobs` - List all processing jobs
- `POST /api/v1/content/search` - Search processed content
- `GET /api/v1/content` - List manual content with filters
- `GET /api/v1/quality/report` - Generate quality report

## Installation

### Requirements

- Python 3.11+
- PostgreSQL 15+
- ChromaDB 0.4.15
- FastAPI 0.104.1

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/bmad_dev"
export CHROMADB_HOST="localhost"
export CHROMADB_PORT="8000"
```

3. Run the service:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8005
```

### Docker Deployment

```bash
docker build -t manual-processing .
docker run -p 8005:8005 manual-processing
```

## Configuration

Key configuration options in `src/config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_FILE_SIZE_MB` | 50 | Maximum PDF file size |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `MIN_READABILITY_SCORE` | 0.3 | Minimum quality threshold |
| `MAX_CHUNK_SIZE` | 1000 | Maximum text chunk size |
| `PROCESSING_TIMEOUT_SECONDS` | 300 | Processing timeout |

## Usage

### Upload PDF Manual

```bash
curl -X POST "http://localhost:8005/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@manual.pdf"
```

### Check Processing Status

```bash
curl "http://localhost:8005/api/v1/status/{job_id}"
```

### Search Content

```bash
curl -X POST "http://localhost:8005/api/v1/content/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "troubleshooting washing machine", "max_results": 10}'
```

## Testing

Run the test suite:

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=src --cov-report=html
```

### Test Structure

- `tests/test_pdf_processor.py` - PDF processing pipeline tests
- `tests/test_text_cleaner.py` - Text cleaning and validation tests
- `tests/test_quality_validator.py` - Quality assurance tests
- `tests/test_integration.py` - Full integration tests

## Quality Assurance

The service implements comprehensive quality checks:

- **Text Quality**: Readability scoring and artifact detection
- **Duplicate Detection**: Content similarity analysis
- **Metadata Validation**: Manufacturer and model verification
- **Performance Monitoring**: Processing time and error tracking

### Quality Metrics

- **Confidence Score**: 0-1 scale for content quality
- **Similarity Threshold**: 0.9 for duplicate detection
- **Response Time**: <2 seconds for search operations
- **Coverage Target**: 90% for core business logic

## Monitoring

Health check endpoint provides service status:

```bash
curl "http://localhost:8005/health"
```

Returns:
- Database connectivity status
- ChromaDB connection status
- Upload directory accessibility
- Response time metrics

## Integration

### ChromaDB Integration

The service integrates with ChromaDB for vector storage:

- HTTP API v1 endpoints
- Collection management
- Vector similarity search
- Metadata filtering

### Database Schema

Manual content stored in PostgreSQL:

```sql
CREATE TABLE manual_content (
    id UUID PRIMARY KEY,
    manufacturer VARCHAR(100) NOT NULL,
    model_series VARCHAR(100) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    source_manual VARCHAR(255),
    page_reference VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Admin Interface

React components for content management:

- **ManualUpload**: Drag-and-drop PDF upload
- **ProcessingStatus**: Real-time job monitoring
- **ContentManagement**: Search and manage processed content
- **QualityAnalytics**: Quality metrics dashboard

## Error Handling

The service implements comprehensive error handling:

- **PDF Processing Errors**: Corrupted files, extraction failures
- **Database Errors**: Connection issues, constraint violations
- **ChromaDB Errors**: Fallback to PostgreSQL text search
- **Validation Errors**: File size, type, content quality

## Performance

Optimization strategies:

- **Async Processing**: Background job execution
- **Batch Embeddings**: Process multiple chunks together
- **Connection Pooling**: Database and HTTP connections
- **Caching**: Quality scores and embeddings
- **Chunking**: Split large documents efficiently

## Contributing

1. Follow coding standards in `docs/architecture/coding-standards.md`
2. Add tests for new functionality
3. Update documentation
4. Run quality checks: `ruff check src/`
5. Ensure 90% test coverage

## License

Part of the BMAD troubleshooting system.