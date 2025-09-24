# Story 1.5 Vector Database Infrastructure - Testing Workflow

## Overview

This document provides a comprehensive testing workflow for Story 1.5: Vector Database Infrastructure. The testing suite validates all 5 acceptance criteria through unit tests, integration tests, performance tests, and end-to-end scenarios.

## Test Suite Structure

```
tests/
├── conftest.py                           # Pytest configuration and fixtures
├── test_story_1_5_vector_infrastructure.py # Comprehensive unit tests (5 ACs)
├── test_chromadb_integration.py          # Integration tests with live ChromaDB
├── test_vector_performance.py            # Performance tests (<2s requirement)
└── STORY_1_5_TESTING_WORKFLOW.md        # This documentation
```

## Acceptance Criteria Coverage

### AC1: ChromaDB Installation & Configuration
- **Tests**: `TestChromaDBInstallationConfiguration`
- **Coverage**: Client initialization, health checks, Docker configuration
- **Files**: `test_story_1_5_vector_infrastructure.py:23-107`

### AC2: Production Deployment Setup
- **Tests**: `TestProductionDeploymentSetup`
- **Coverage**: Railway config, persistent storage, backup procedures
- **Files**: `test_story_1_5_vector_infrastructure.py:109-162`

### AC3: Basic Vector Operations
- **Tests**: `TestBasicVectorOperations`
- **Coverage**: CRUD operations, performance benchmarking, error handling
- **Files**: `test_story_1_5_vector_infrastructure.py:164-351`

### AC4: Integration Preparation
- **Tests**: `TestIntegrationPreparation`
- **Coverage**: API client, monitoring, documentation
- **Files**: `test_story_1_5_vector_infrastructure.py:353-420`

### AC5: Development Environment Validation
- **Tests**: `TestDevelopmentEnvironmentValidation`
- **Coverage**: Local setup, test data loading, developer docs
- **Files**: `test_story_1_5_vector_infrastructure.py:422-495`

## Prerequisites

### Environment Setup

1. **Python Environment**:
   ```bash
   # Ensure Python 3.8+ with required packages
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

2. **Project Dependencies**:
   ```bash
   # Install project dependencies
   pip install -r requirements.txt
   # Or for semantic search service:
   pip install -r services/semantic-search/requirements.txt
   ```

3. **ChromaDB Service** (for integration tests):
   ```bash
   # Option A: Docker Compose
   docker-compose up chromadb

   # Option B: Direct Docker
   docker run -p 8000:8000 chromadb/chroma:0.4.15

   # Option C: Local installation
   pip install chromadb==0.4.15
   chroma run --host localhost --port 8000
   ```

4. **Semantic Search Service** (for integration tests):
   ```bash
   # Start the service
   cd services/semantic-search
   python simple_main.py
   # Service runs on localhost:8004
   ```

### Environment Variables

Set these environment variables for customized testing:

```bash
# ChromaDB Configuration
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8000

# Semantic Search Configuration
export SEMANTIC_SEARCH_HOST=localhost
export SEMANTIC_SEARCH_PORT=8004

# Test Configuration
export PYTHONPATH=.:tests
```

## Test Execution

### Run All Tests

```bash
# Run complete test suite
cd tests
pytest -v

# Run with coverage report
pytest -v --cov=shared.python.database.vector_client --cov=services.semantic_search --cov-report=html
```

### Run by Test Category

```bash
# Unit tests only (no external dependencies)
pytest -v -m "not integration and not performance"

# Integration tests (requires ChromaDB running)
pytest -v -m integration

# Performance tests (requires ChromaDB with test data)
pytest -v -m performance

# Story 1.5 specific tests
pytest -v -m story_1_5

# ChromaDB specific tests
pytest -v -m chromadb
```

### Run Individual Test Files

```bash
# Comprehensive Story 1.5 tests
pytest -v test_story_1_5_vector_infrastructure.py

# Integration tests
pytest -v test_chromadb_integration.py

# Performance tests
pytest -v test_vector_performance.py
```

### Run Specific Test Classes

```bash
# Test ChromaDB installation
pytest -v test_story_1_5_vector_infrastructure.py::TestChromaDBInstallationConfiguration

# Test vector operations
pytest -v test_story_1_5_vector_infrastructure.py::TestBasicVectorOperations

# Test integration scenarios
pytest -v test_chromadb_integration.py::TestChromaDBHTTPIntegration
```

## Test Scenarios

### Unit Test Scenarios (No External Dependencies)

```bash
# Run unit tests with mocking
pytest -v test_story_1_5_vector_infrastructure.py -k "not integration"
```

**Covered Scenarios**:
- ChromaDB client initialization with mocked dependencies
- Vector operations with mocked responses
- Error handling with simulated failures
- Configuration validation
- API model validation

### Integration Test Scenarios (Requires Services)

```bash
# Ensure ChromaDB is running on localhost:8000
pytest -v test_chromadb_integration.py
```

**Covered Scenarios**:
- Real ChromaDB HTTP API operations
- Collection lifecycle (create, populate, query, delete)
- Semantic search service integration
- Concurrent operations testing
- Error handling with real service responses

### Performance Test Scenarios (Load Testing)

```bash
# Run performance tests with detailed output
pytest -v -s test_vector_performance.py
```

**Covered Scenarios**:
- Single query performance (<2 second requirement)
- Concurrent query performance under load
- Large result set performance
- Sustained load testing (30 seconds)
- Performance metrics collection

## Expected Results

### Success Criteria

All tests should pass with the following characteristics:

1. **Unit Tests**: 100% pass rate with proper mocking
2. **Integration Tests**: 95%+ pass rate (allows for service availability)
3. **Performance Tests**: All queries under 2 second limit
4. **Coverage**: 90%+ line coverage for core business logic

### Performance Benchmarks

- **Single Query**: <2 seconds (requirement)
- **Average Query**: <1 second (target)
- **95th Percentile**: <1.5 seconds (target)
- **Concurrent Load**: 95%+ success rate
- **Sustained Load**: 30 seconds with consistent performance

### Sample Output

```
=== Story 1.5 Vector Database Infrastructure Test Suite ===
Validating test environment...
Project root: /path/to/BMAD
✓ Vector client module available
✓ ChromaDB service available at http://localhost:8000/api/v1/heartbeat
✓ Semantic Search service available at http://localhost:8004/health
Test environment validation complete.

tests/test_story_1_5_vector_infrastructure.py::TestChromaDBInstallationConfiguration::test_chromadb_client_initialization PASSED
tests/test_story_1_5_vector_infrastructure.py::TestChromaDBInstallationConfiguration::test_chromadb_health_check_endpoint PASSED
tests/test_story_1_5_vector_infrastructure.py::TestBasicVectorOperations::test_create_collection_with_embeddings PASSED
tests/test_story_1_5_vector_infrastructure.py::TestBasicVectorOperations::test_vector_similarity_search_performance PASSED

Performance Test Results:
Average query time: 0.234s
  'vector database optimization performance': 0.198s (3 results)
  'semantic search large scale datasets': 0.287s (5 results)
  'API framework high performance design': 0.201s (4 results)

=== 45 passed, 3 skipped in 12.34s ===
Coverage: 92% (234/255 lines)
```

## Troubleshooting

### Common Issues

#### ChromaDB Connection Failed
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Start ChromaDB if not running
docker run -p 8000:8000 chromadb/chroma:0.4.15
```

#### Import Errors
```bash
# Ensure Python path includes project root
export PYTHONPATH=.:tests:shared/python
```

#### Performance Tests Failing
```bash
# Check system resources
htop  # Ensure sufficient CPU/memory

# Run performance tests with longer timeouts
pytest -v test_vector_performance.py --timeout=60
```

#### Module Not Found Errors
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Install project dependencies
pip install -r requirements.txt
```

### Debugging Test Failures

#### Enable Debug Logging
```bash
# Run tests with debug output
pytest -v -s --log-cli-level=DEBUG test_story_1_5_vector_infrastructure.py
```

#### Run Individual Failing Tests
```bash
# Run specific failing test with full traceback
pytest -v --tb=long test_story_1_5_vector_infrastructure.py::TestBasicVectorOperations::test_vector_similarity_search_performance
```

#### Check Service Health
```bash
# Test ChromaDB directly
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "metadata": {}}'

# Test Semantic Search service
curl http://localhost:8004/health
```

### Skip Tests for Unavailable Services

Tests automatically skip when services are unavailable:

```python
# Integration tests skip if ChromaDB not running
@pytest.mark.integration
async def test_chromadb_integration():
    try:
        # Test ChromaDB operations
        pass
    except httpx.ConnectError:
        pytest.skip("ChromaDB not available")
```

## Test Data Management

### Test Collections

Tests create temporary collections with names like:
- `test_collection_{timestamp}_{uuid}`
- `performance_test_{timestamp}`
- `integration_test_{timestamp}`

### Cleanup

- Tests automatically clean up created collections
- Failed tests may leave test data (check ChromaDB)
- Manual cleanup:
  ```bash
  # List all collections
  curl http://localhost:8000/api/v1/collections

  # Delete test collection
  curl -X DELETE http://localhost:8000/api/v1/collections/test_collection_123
  ```

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Story 1.5 Vector Database Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      chromadb:
        image: chromadb/chroma:0.4.15
        ports:
          - 8000:8000

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install pytest pytest-asyncio pytest-cov httpx
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd tests
        pytest -v --cov=shared.python.database.vector_client --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Metrics and Reporting

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=shared.python.database.vector_client --cov=services.semantic_search --cov-report=html

# View report
open htmlcov/index.html
```

### Performance Report

```bash
# Run performance tests with detailed timing
pytest -v -s test_vector_performance.py > performance_report.txt

# Performance metrics saved to report
cat performance_report.txt
```

### Test Results Summary

The test suite provides comprehensive validation that:

1. ✅ ChromaDB 0.4.15 is properly installed and configured
2. ✅ Production deployment setup is ready for Railway/Render
3. ✅ Vector operations (CRUD) work correctly with <2s performance
4. ✅ Integration infrastructure is prepared for semantic search
5. ✅ Development environment is validated and documented

This testing workflow ensures Story 1.5 meets all acceptance criteria and is ready for Epic 2 semantic search implementation.

## Maintenance

### Updating Tests

When updating the vector database implementation:

1. Update test fixtures in `conftest.py`
2. Add new test scenarios for new features
3. Update performance benchmarks if requirements change
4. Update this documentation

### Test Data Refresh

Periodically refresh test data:

```bash
# Update sample documents in conftest.py
# Update performance test datasets
# Clear any persistent test collections
```

---

**Last Updated**: 2025-09-24
**Version**: 1.0
**Maintainer**: BMAD Development Team