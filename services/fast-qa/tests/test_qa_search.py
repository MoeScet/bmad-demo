"""
Tests for Q&A search endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from models.qa_entry import QAEntry


def test_search_qa_entries_basic(client: TestClient, multiple_qa_entries):
    """Test basic Q&A search functionality."""
    response = client.post("/qa/search", json={
        "query": "washing machine start",
        "max_results": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    assert "data" in data
    assert "results" in data["data"]
    assert "total_count" in data["data"]
    assert "query_time_ms" in data["data"]
    
    # Should find at least one relevant result
    results = data["data"]["results"]
    assert len(results) > 0
    
    # Check result structure
    first_result = results[0]
    assert "entry" in first_result
    assert "relevance_score" in first_result
    assert "match_type" in first_result
    
    # Check entry structure
    entry = first_result["entry"]
    assert "id" in entry
    assert "question" in entry
    assert "answer" in entry
    assert "safety_level" in entry


def test_search_qa_entries_with_filters(client: TestClient, multiple_qa_entries):
    """Test Q&A search with safety level filters."""
    response = client.post("/qa/search", json={
        "query": "machine",
        "max_results": 5,
        "safety_levels": ["safe"],
        "min_score": 0.2
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    results = data["data"]["results"]
    
    # All results should have safe safety level
    for result in results:
        assert result["entry"]["safety_level"] == "safe"


def test_search_qa_entries_empty_query(client: TestClient):
    """Test search with empty query."""
    response = client.post("/qa/search", json={
        "query": "   ",
        "max_results": 10
    })
    
    # Should return validation error for empty query
    assert response.status_code == 422


def test_search_qa_entries_no_results(client: TestClient, multiple_qa_entries):
    """Test search that returns no results."""
    response = client.post("/qa/search", json={
        "query": "nonexistent topic that should not match",
        "max_results": 10,
        "min_score": 0.9
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    assert data["data"]["total_count"] == 0
    assert len(data["data"]["results"]) == 0


def test_search_qa_entries_relevance_scoring(client: TestClient, multiple_qa_entries):
    """Test that search results are properly scored and ordered."""
    response = client.post("/qa/search", json={
        "query": "drain",
        "max_results": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    
    results = data["data"]["results"]
    if len(results) > 1:
        # Results should be ordered by relevance score (descending)
        for i in range(len(results) - 1):
            assert results[i]["relevance_score"] >= results[i + 1]["relevance_score"]


def test_search_qa_entries_max_results_limit(client: TestClient, multiple_qa_entries):
    """Test max_results parameter limits results correctly."""
    response = client.post("/qa/search", json={
        "query": "machine",
        "max_results": 2
    })
    
    assert response.status_code == 200
    data = response.json()
    
    results = data["data"]["results"]
    assert len(results) <= 2


def test_get_qa_entry_by_id(client: TestClient, sample_qa_entry):
    """Test retrieving a specific Q&A entry by ID."""
    response = client.get(f"/qa/{sample_qa_entry.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    entry_data = data["data"]
    assert entry_data["id"] == str(sample_qa_entry.id)
    assert entry_data["question"] == sample_qa_entry.question
    assert entry_data["answer"] == sample_qa_entry.answer


def test_get_qa_entry_not_found(client: TestClient):
    """Test retrieving a non-existent Q&A entry."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/qa/{fake_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"] is None
    assert data["error"]["code"] == "ENTRY_NOT_FOUND"
    assert fake_id in data["error"]["entry_id"]


def test_search_with_correlation_id(client: TestClient, sample_qa_entry):
    """Test search request with correlation ID header."""
    correlation_id = str(uuid.uuid4())
    
    response = client.post("/qa/search", 
        json={"query": "start", "max_results": 5},
        headers={"X-Correlation-ID": correlation_id}
    )
    
    assert response.status_code == 200
    # The correlation ID should be used internally for logging
    # but doesn't affect the response structure


def test_search_performance(client: TestClient, multiple_qa_entries):
    """Test that search performance meets requirements."""
    response = client.post("/qa/search", json={
        "query": "machine noise problem",
        "max_results": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Query should complete within reasonable time (< 3000ms for test environment)
    query_time = data["data"]["query_time_ms"]
    assert query_time < 3000  # 3 seconds should be more than enough for test DB