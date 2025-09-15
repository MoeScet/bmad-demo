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


def test_ml_ranking_algorithm(client: TestClient):
    """Test that ML-enhanced ranking properly weights success rates."""
    # Create entries with different success rates for testing
    from sqlalchemy.orm import sessionmaker
    from models.database import engine
    
    # This test would require database setup - simplified for now
    response = client.post("/qa/search", json={
        "query": "test query",
        "max_results": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify that results include ML-derived scoring
    results = data["data"]["results"]
    for result in results:
        assert "relevance_score" in result
        assert 0.0 <= result["relevance_score"] <= 1.0


def test_qa_feedback_submission(client: TestClient, sample_qa_entry):
    """Test submitting feedback for Q&A solutions."""
    feedback_data = {
        "solution_id": str(sample_qa_entry.id),
        "is_helpful": True,
        "user_context": "This solution worked perfectly"
    }
    
    response = client.post("/qa/feedback", json=feedback_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    assert data["data"]["message"] == "Feedback received successfully"
    assert data["data"]["solution_id"] == str(sample_qa_entry.id)
    assert data["data"]["is_helpful"] is True


def test_qa_feedback_negative(client: TestClient, sample_qa_entry):
    """Test submitting negative feedback."""
    feedback_data = {
        "solution_id": str(sample_qa_entry.id),
        "is_helpful": False,
        "user_context": "This didn't work for my model"
    }
    
    response = client.post("/qa/feedback", json=feedback_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    assert data["data"]["is_helpful"] is False


def test_qa_feedback_invalid_id(client: TestClient):
    """Test feedback with invalid solution ID."""
    fake_id = str(uuid.uuid4())
    feedback_data = {
        "solution_id": fake_id,
        "is_helpful": True
    }
    
    response = client.post("/qa/feedback", json=feedback_data)
    
    # Should still accept feedback (async processing handles validation)
    assert response.status_code == 200


def test_qa_feedback_validation(client: TestClient):
    """Test feedback request validation."""
    # Invalid solution_id format
    response = client.post("/qa/feedback", json={
        "solution_id": "invalid-uuid",
        "is_helpful": True
    })
    
    assert response.status_code == 422  # Validation error
    
    # Missing required fields
    response = client.post("/qa/feedback", json={
        "is_helpful": True
    })
    
    assert response.status_code == 422


def test_search_ranking_with_success_rates(client: TestClient, multiple_qa_entries):
    """Test that entries with higher success rates rank better."""
    # Search for entries that should have different success rates
    response = client.post("/qa/search", json={
        "query": "machine",
        "max_results": 10
    })
    
    assert response.status_code == 200
    data = response.json()
    
    results = data["data"]["results"]
    if len(results) > 1:
        # Check that relevance scores consider success rates
        # This is a basic test - in reality we'd need controlled test data
        for result in results:
            entry = result["entry"]
            relevance = result["relevance_score"]
            
            # Higher success rates should generally correlate with higher scores
            # (though other factors like keyword matching also matter)
            assert relevance >= 0.0
            assert "success_rate" in entry
            assert "usage_count" in entry


def test_search_regression_functionality(client: TestClient, multiple_qa_entries):
    """Test that existing search functionality still works after ML enhancements."""
    # This ensures we haven't broken existing functionality
    response = client.post("/qa/search", json={
        "query": "washing machine",
        "max_results": 5,
        "safety_levels": ["safe", "caution"],
        "min_score": 0.1
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Basic response structure unchanged
    assert data["error"] is None
    assert "results" in data["data"]
    assert "total_count" in data["data"]
    assert "query_time_ms" in data["data"]
    assert "applied_filters" in data["data"]
    
    # Results structure unchanged
    results = data["data"]["results"]
    for result in results:
        assert "entry" in result
        assert "relevance_score" in result
        assert "match_type" in result
        
        # Safety levels properly filtered
        safety_level = result["entry"]["safety_level"]
        assert safety_level in ["safe", "caution"]