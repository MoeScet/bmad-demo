# Developer Guide: Vector Database Operations

## Overview

This guide provides developers with everything needed to work with ChromaDB vector database operations in the BMAD troubleshooting system. It covers setup, usage patterns, testing, and best practices.

## Quick Start

### 1. Environment Setup

```bash
# Start local development environment
docker-compose up chromadb postgres

# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Validate environment
python scripts/validate_development_environment.py --report
```

### 2. Basic Usage

```python
# Import vector client
from shared.python.database import get_vector_client

# Use vector database
async def example_usage():
    async with get_vector_client() as client:
        # Create collection
        collection_id = await client.create_collection("my_collection")

        # Add documents
        doc_ids = await client.add_embeddings(
            "my_collection",
            ["Document 1 content", "Document 2 content"],
            metadatas=[{"type": "example"}, {"type": "example"}]
        )

        # Search similar documents
        results = await client.search_similar(
            "my_collection",
            "search query text",
            n_results=5
        )

        print(f"Found {len(results['documents'])} similar documents")
```

### 3. Test Your Setup

```bash
# Run basic vector operations test
python scripts/test_chromadb.py

# Run with custom parameters
python scripts/test_chromadb.py --host localhost --port 8000 --benchmark

# Validate development environment
python scripts/validate_development_environment.py
```

## Core Concepts

### Vector Embeddings

Vector embeddings convert text into high-dimensional numerical representations that capture semantic meaning:

```python
# Text -> Vector conversion happens automatically
documents = [
    "FastAPI is a web framework",
    "ChromaDB stores vector embeddings",
    "Semantic search finds similar content"
]

# ChromaDBClient handles embedding generation internally
async with get_vector_client() as client:
    doc_ids = await client.add_embeddings("collection", documents)
    # Documents are now stored as 384-dimensional vectors
```

### Similarity Search

Search finds documents with similar semantic meaning, not just keyword matches:

```python
# These queries will find semantically similar content
search_queries = [
    "web development framework",        # Finds FastAPI content
    "vector database storage",          # Finds ChromaDB content
    "finding relevant documents"        # Finds semantic search content
]

for query in search_queries:
    results = await client.search_similar("collection", query, n_results=3)
    # Returns documents ranked by semantic similarity
```

### Collections

Collections organize related documents and embeddings:

```python
# Different collections for different content types
collections = {
    "troubleshooting_manuals": "Technical documentation",
    "faq_content": "Frequently asked questions",
    "code_examples": "Programming examples",
    "test_data": "Development and testing content"
}

for name, description in collections.items():
    await client.create_collection(name, metadata={"description": description})
```

## API Reference

### ChromaDBClient Class

The main interface for vector database operations:

```python
from shared.python.database.vector_client import ChromaDBClient, get_vector_client

# Direct instantiation
client = ChromaDBClient(host="localhost", port=8000)
await client.initialize()

# Context manager (recommended)
async with get_vector_client() as client:
    # Client is automatically initialized and cleaned up
    pass
```

### Core Methods

#### Collection Management

```python
# Create collection
collection_id = await client.create_collection(
    collection_name="my_docs",
    metadata={"version": "1.0", "type": "documentation"},
    correlation_id="optional-trace-id"
)

# Get collection information
info = await client.get_collection_info("my_docs")
print(f"Collection has {info['count']} documents")

# Delete collection
success = await client.delete_collection("my_docs")
```

#### Document Operations

```python
# Add documents with embeddings
doc_ids = await client.add_embeddings(
    collection_name="my_docs",
    documents=["Content 1", "Content 2", "Content 3"],
    metadatas=[
        {"category": "api", "priority": "high"},
        {"category": "guide", "priority": "medium"},
        {"category": "example", "priority": "low"}
    ],
    ids=["doc_1", "doc_2", "doc_3"],  # Optional custom IDs
    correlation_id="batch-insert-123"
)
```

#### Search Operations

```python
# Basic similarity search
results = await client.search_similar(
    collection_name="my_docs",
    query="how to configure API endpoints",
    n_results=10,
    correlation_id="search-456"
)

# Access results
for i, doc in enumerate(results["documents"]):
    similarity = 1.0 - results["distances"][i]  # Convert distance to similarity
    metadata = results["metadatas"][i]
    doc_id = results["ids"][i]

    print(f"Document {doc_id}: {similarity:.3f} similarity")
    print(f"Content: {doc[:100]}...")
    print(f"Metadata: {metadata}")

# Advanced search with metadata filtering
results = await client.search_similar(
    collection_name="my_docs",
    query="API configuration",
    n_results=5,
    where={"category": "api"}  # Filter by metadata
)
```

#### Health Monitoring

```python
# Check database health
health = await client.health_check()
if health["status"] == "healthy":
    print("ChromaDB is operational")
else:
    print(f"ChromaDB issue: {health}")
```

### Error Handling

All vector operations use proper error handling with fallback responses:

```python
from shared.python.database import VectorDatabaseError

try:
    results = await client.search_similar("collection", "query")

except VectorDatabaseError as e:
    # Handle gracefully - error messages are user-safe
    if "knowledge gap" in str(e):
        # Vector database unavailable - use fallback
        results = {"documents": [], "message": "Search temporarily unavailable"}

except asyncio.TimeoutError:
    # Search took too long - enforce 2-second limit
    results = {"documents": [], "message": "Search timeout - try a simpler query"}
```

## Configuration

### Environment Variables

Configure vector database connection and behavior:

```bash
# ChromaDB Connection
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=bmad_embeddings

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
MAX_EMBEDDING_BATCH_SIZE=32

# Search Configuration
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=10
SEMANTIC_SEARCH_TIMEOUT=12.0
```

### Service Configuration

```python
# Custom configuration for your service
from shared.python.config.base import VectorDatabaseConfig

class MyServiceConfig(VectorDatabaseConfig):
    SERVICE_NAME: str = "my-service"
    DEFAULT_COLLECTION: str = "my_service_docs"
    CUSTOM_SIMILARITY_THRESHOLD: float = 0.8

settings = MyServiceConfig()
```

## Testing Guide

### Unit Testing

Test vector operations in isolation:

```python
import pytest
from shared.python.database import get_vector_client, VectorDatabaseError

@pytest.mark.asyncio
async def test_vector_search():
    """Test basic vector search functionality"""
    async with get_vector_client() as client:
        # Setup test collection
        test_collection = "test_search"
        await client.create_collection(test_collection)

        # Add test documents
        docs = ["Python programming", "Web development", "Database design"]
        await client.add_embeddings(test_collection, docs)

        # Test search
        results = await client.search_similar(
            test_collection,
            "software development",
            n_results=2
        )

        # Assertions
        assert len(results["documents"]) == 2
        assert all(isinstance(d, str) for d in results["documents"])
        assert all(0.0 <= score <= 1.0 for score in results["distances"])

        # Cleanup
        await client.delete_collection(test_collection)

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for missing collections"""
    async with get_vector_client() as client:
        with pytest.raises(VectorDatabaseError):
            await client.search_similar("nonexistent", "query")
```

### Integration Testing

Test end-to-end workflows:

```python
@pytest.mark.asyncio
async def test_semantic_search_service():
    """Test semantic search service integration"""
    import httpx

    async with httpx.AsyncClient() as http_client:
        # Test service health
        response = await http_client.get("http://localhost:8004/health")
        assert response.status_code == 200

        # Test search endpoint
        search_request = {
            "query": "API development best practices",
            "max_results": 5,
            "similarity_threshold": 0.6
        }

        response = await http_client.post(
            "http://localhost:8004/api/v1/search",
            json=search_request
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "search_time_ms" in data
        assert data["search_time_ms"] < 2000  # <2s requirement
```

### Performance Testing

Validate performance requirements:

```bash
# Run performance benchmarks
python scripts/test_chromadb.py --benchmark --benchmark-size 1000

# Validate search latency
python scripts/validate_development_environment.py --host localhost --port 8000
```

## Best Practices

### 1. Use Context Managers

Always use `get_vector_client()` context manager for automatic cleanup:

```python
# ✅ Recommended
async with get_vector_client() as client:
    results = await client.search_similar("collection", "query")

# ❌ Avoid manual management
client = ChromaDBClient()
await client.initialize()
results = await client.search_similar("collection", "query")
# Cleanup not guaranteed
```

### 2. Handle Errors Gracefully

Implement proper fallback responses:

```python
async def search_with_fallback(query: str) -> List[str]:
    try:
        async with get_vector_client() as client:
            results = await client.search_similar("docs", query)
            return results["documents"]

    except VectorDatabaseError:
        # Vector database unavailable - use fallback
        return await fallback_search(query)

    except asyncio.TimeoutError:
        # Search too slow - return empty results
        return []
```

### 3. Use Correlation IDs

Include correlation IDs for request tracing:

```python
async def traced_search(query: str, correlation_id: str):
    async with get_vector_client() as client:
        return await client.search_similar(
            "collection",
            query,
            correlation_id=correlation_id
        )
```

### 4. Optimize Batch Operations

Process documents in batches for better performance:

```python
async def add_documents_batch(documents: List[str], batch_size: int = 32):
    async with get_vector_client() as client:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            await client.add_embeddings("collection", batch)
            print(f"Processed batch {i//batch_size + 1}")
```

### 5. Use Appropriate Similarity Thresholds

Choose thresholds based on use case:

```python
# High precision - exact matches only
high_precision_results = await search_filtered(query, threshold=0.8)

# Balanced - general use
balanced_results = await search_filtered(query, threshold=0.6)

# High recall - exploratory search
exploratory_results = await search_filtered(query, threshold=0.4)

async def search_filtered(query: str, threshold: float):
    async with get_vector_client() as client:
        results = await client.search_similar("docs", query, n_results=20)

        # Filter by similarity threshold
        filtered = []
        for i, doc in enumerate(results["documents"]):
            similarity = 1.0 - results["distances"][i]
            if similarity >= threshold:
                filtered.append({
                    "document": doc,
                    "similarity": similarity,
                    "metadata": results["metadatas"][i]
                })

        return filtered
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```bash
# Check if ChromaDB is running
docker-compose ps chromadb

# View ChromaDB logs
docker-compose logs chromadb

# Restart ChromaDB service
docker-compose restart chromadb
```

#### 2. Slow Search Performance

```python
# Check collection size
async with get_vector_client() as client:
    info = await client.get_collection_info("my_collection")
    print(f"Collection size: {info['count']} documents")

# Large collections (>100K docs) may need optimization
# Consider collection partitioning or indexing strategies
```

#### 3. Memory Issues

```bash
# Monitor Docker memory usage
docker stats

# Increase Docker memory limit if needed
# Or reduce embedding batch sizes
```

#### 4. Import Errors

```python
# Ensure shared library is in Python path
import sys
sys.path.append('/path/to/bmad/shared/python')

from shared.python.database import get_vector_client
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Vector client operations will show detailed logs
async with get_vector_client() as client:
    results = await client.search_similar("collection", "query")
```

### Performance Monitoring

Monitor vector database performance:

```python
import time

async def monitored_search(query: str):
    start_time = time.time()

    async with get_vector_client() as client:
        results = await client.search_similar("docs", query)

    search_time = time.time() - start_time

    # Log performance metrics
    print(f"Search completed in {search_time:.3f}s")
    print(f"Results: {len(results['documents'])}")

    # Alert if performance degrades
    if search_time > 2.0:
        print("⚠️ Search performance degraded - investigate")

    return results
```

## Advanced Usage

### Custom Collections

Create specialized collections for different content types:

```python
async def setup_specialized_collections():
    async with get_vector_client() as client:
        # Technical documentation
        await client.create_collection(
            "technical_docs",
            metadata={
                "type": "documentation",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "preprocessing": "technical_terms_preserved"
            }
        )

        # FAQ content
        await client.create_collection(
            "faq_content",
            metadata={
                "type": "qa_pairs",
                "chunk_strategy": "question_answer_pairs"
            }
        )

        # Code examples
        await client.create_collection(
            "code_examples",
            metadata={
                "type": "source_code",
                "language": "python",
                "preprocessing": "code_comments_extracted"
            }
        )
```

### Multi-Collection Search

Search across multiple collections:

```python
async def multi_collection_search(query: str, collections: List[str]):
    all_results = []

    async with get_vector_client() as client:
        for collection in collections:
            try:
                results = await client.search_similar(collection, query, n_results=5)

                # Add collection source to results
                for i, doc in enumerate(results["documents"]):
                    all_results.append({
                        "document": doc,
                        "similarity": 1.0 - results["distances"][i],
                        "collection": collection,
                        "metadata": results["metadatas"][i]
                    })

            except VectorDatabaseError:
                # Skip unavailable collections
                continue

    # Sort by similarity across all collections
    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    return all_results[:10]  # Top 10 across all collections
```

### Real-time Updates

Handle real-time document updates:

```python
async def update_document(doc_id: str, new_content: str, collection: str):
    async with get_vector_client() as client:
        # ChromaDB doesn't support direct updates, so delete and re-add
        # In production, implement versioning strategy

        # Add new version
        await client.add_embeddings(
            collection,
            [new_content],
            metadatas=[{"id": doc_id, "updated_at": time.time()}],
            ids=[f"{doc_id}_v2"]
        )

        # Mark old version as deprecated (metadata update)
        # Real implementation would need custom indexing strategy
```

## Production Considerations

### Performance Optimization

1. **Batch Processing**: Process embeddings in batches of 32-64 documents
2. **Connection Pooling**: Reuse connections for multiple operations
3. **Caching**: Cache frequent search results in Redis
4. **Monitoring**: Track search latency and collection sizes

### Security

1. **Network Security**: Use private networking between services
2. **Data Sanitization**: Remove PII before embedding
3. **Access Control**: Implement service-to-service authentication
4. **Audit Logging**: Log all search operations with correlation IDs

### Scalability

1. **Collection Partitioning**: Split large collections by category
2. **Horizontal Scaling**: Deploy multiple ChromaDB instances
3. **Load Balancing**: Distribute search requests across instances
4. **Edge Deployment**: Deploy ChromaDB close to users for latency

This guide covers the essential patterns for working with vector databases in BMAD. For specific implementation questions, refer to the API documentation and test examples in the `scripts/` directory.