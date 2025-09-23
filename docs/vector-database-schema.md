# Vector Database Schema and Indexing Strategy

## Overview

This document defines the ChromaDB vector database schema, indexing strategy, and collection management for the BMAD troubleshooting system.

## Collection Schema

### Primary Collection: `manual_content_embeddings`

**Purpose**: Store embeddings for manual troubleshooting content from PostgreSQL database

**Schema**:
```json
{
  "collection_name": "manual_content_embeddings",
  "metadata": {
    "description": "Troubleshooting manual content embeddings",
    "version": "1.0",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "created_at": "2025-09-23T00:00:00Z"
  }
}
```

**Document Structure**:
```json
{
  "id": "manual_content_{postgresql_id}",
  "document": "Full text content from manual_content table",
  "metadata": {
    "source_id": 123,
    "title": "Document title",
    "category": "troubleshooting_category",
    "created_at": "2025-09-23T00:00:00Z",
    "updated_at": "2025-09-23T00:00:00Z",
    "content_hash": "sha256_hash_of_content",
    "embedding_version": "1.0"
  }
}
```

### Test Collection: `test_embeddings`

**Purpose**: Testing and validation of vector operations

**Schema**:
```json
{
  "collection_name": "test_embeddings",
  "metadata": {
    "description": "Test collection for vector operations validation",
    "version": "1.0",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "is_test": true
  }
}
```

## Embedding Strategy

### Model Configuration

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimension**: 384
- **Language**: English
- **Context Length**: 256 tokens
- **Normalization**: L2 normalized embeddings

### Preprocessing Pipeline

1. **Text Cleaning**
   - Remove HTML tags and special characters
   - Normalize whitespace
   - Preserve technical terminology
   - Truncate to 256 tokens

2. **Chunking Strategy**
   - Split documents >256 tokens into overlapping chunks
   - Overlap: 32 tokens
   - Maintain sentence boundaries
   - Preserve context for technical content

3. **Metadata Enrichment**
   - Extract technical keywords
   - Identify troubleshooting categories
   - Add content classification tags

### Embedding Generation

```python
# Example embedding generation
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embeddings = model.encode(documents, normalize_embeddings=True)
```

## Indexing Strategy

### Performance Optimization

- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine similarity
- **Search Algorithm**: Approximate k-NN with HNSW index
- **Performance Target**: <2 seconds for similarity search

### Collection Partitioning

Collections organized by:
1. **Content Type**: manual_content, faqs, troubleshooting_steps
2. **Category**: hardware, software, network, security
3. **Update Frequency**: static, dynamic, real-time

### Index Maintenance

- **Rebuild Frequency**: Weekly for production collections
- **Incremental Updates**: Real-time for new documents
- **Optimization**: Background re-indexing during low usage periods

## Search Configuration

### Similarity Thresholds

| Use Case | Threshold | Rationale |
|----------|-----------|-----------|
| **High Precision** | 0.8+ | Exact match scenarios |
| **Balanced** | 0.6-0.8 | General troubleshooting |
| **High Recall** | 0.4-0.6 | Exploratory search |
| **Fallback** | 0.0-0.4 | No strong matches found |

### Search Parameters

```python
search_config = {
    "n_results": 10,          # Default result count
    "max_results": 50,        # Maximum allowed results
    "similarity_threshold": 0.6,  # Minimum similarity
    "include_metadata": True,     # Return document metadata
    "include_distances": True     # Return similarity scores
}
```

## Data Synchronization

### PostgreSQL to ChromaDB Sync

**Trigger**: Changes to `manual_content` table
**Process**:
1. Detect changes via PostgreSQL triggers
2. Extract modified content
3. Generate new embeddings
4. Update ChromaDB collection
5. Validate embedding integrity

**Sync Schedule**:
- **Real-time**: Critical content updates
- **Batch**: Non-critical updates every 15 minutes
- **Full Sync**: Weekly validation and cleanup

### Change Detection

```sql
-- PostgreSQL trigger for change detection
CREATE OR REPLACE FUNCTION notify_content_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        PERFORM pg_notify('content_change', json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'id', NEW.id,
            'content_hash', md5(NEW.content)
        )::text);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM pg_notify('content_change', json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'id', OLD.id
        )::text);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

## Monitoring and Metrics

### Performance Metrics

- **Search Latency**: P50, P95, P99 response times
- **Throughput**: Queries per second
- **Accuracy**: Search relevance scores
- **Availability**: Service uptime percentage

### Health Indicators

1. **Index Health**
   - Collection size vs expected size
   - Embedding dimension consistency
   - Metadata completeness

2. **Search Quality**
   - Average similarity scores
   - Result distribution
   - User feedback on relevance

3. **System Resources**
   - Memory usage for embeddings
   - Disk space utilization
   - CPU usage during search operations

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| **Search Latency** | >1 second | >2 seconds |
| **Error Rate** | >1% | >5% |
| **Collection Size Drift** | >10% | >25% |
| **Memory Usage** | >80% | >95% |

## Security and Access Control

### Authentication

- **Service-to-Service**: Mutual TLS between BMAD services
- **Internal Network**: Railway private networking
- **API Keys**: Not implemented (internal services only)

### Data Privacy

- **Content Sanitization**: Remove PII before embedding
- **Access Logging**: Log all search queries with correlation IDs
- **Retention Policy**: Embeddings retained according to source data policy

## Backup and Recovery

### Backup Strategy

1. **Collection Snapshots**: Daily automated snapshots
2. **Metadata Backup**: Configuration and schema backups
3. **Embedding Export**: Periodic full collection exports
4. **Source Data**: Rely on PostgreSQL backup for source content

### Recovery Procedures

1. **Collection Restoration**: Restore from Railway volume snapshots
2. **Rebuild from Source**: Regenerate embeddings from PostgreSQL
3. **Incremental Sync**: Sync only changed content after recovery

## Version Management

### Schema Versioning

- **Version Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Migration Strategy**: Blue-green deployment for schema changes
- **Backward Compatibility**: Maintain compatibility for 2 versions

### Embedding Model Updates

1. **New Model Deployment**: Deploy alongside existing model
2. **Parallel Testing**: Compare search quality between models
3. **Gradual Migration**: Migrate collections incrementally
4. **Rollback Plan**: Maintain previous model for quick rollback

## Development and Testing

### Local Development

```bash
# Start ChromaDB locally
docker-compose up chromadb

# Initialize test collection
python scripts/init_test_collection.py

# Run vector operations tests
python scripts/test_chromadb.py --host localhost --port 8000
```

### Testing Strategy

1. **Unit Tests**: Vector client operations
2. **Integration Tests**: End-to-end search workflows
3. **Performance Tests**: Load testing with realistic query patterns
4. **Quality Tests**: Search relevance validation

### Test Data

- **Synthetic Data**: Generated test documents for development
- **Anonymized Production Data**: Sanitized real content for testing
- **Benchmark Queries**: Standard query set for performance validation

## Future Enhancements

### Planned Improvements

1. **Multi-Modal Embeddings**: Support for image and code embeddings
2. **Federated Search**: Cross-collection search capabilities
3. **Real-Time Learning**: Feedback-based embedding refinement
4. **Advanced Filtering**: Complex metadata-based filtering

### Scalability Considerations

1. **Horizontal Scaling**: Multiple ChromaDB instances with load balancing
2. **Collection Sharding**: Split large collections across instances
3. **Caching Layer**: Redis cache for frequent search patterns
4. **Edge Deployment**: Regional ChromaDB deployments for latency optimization