"""
Integration tests for Fast Q&A Service.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient


def test_end_to_end_workflow(client: TestClient):
    """Test complete workflow: create, search, update, delete."""
    
    # 1. Create a new entry
    entry_data = {
        "question": "How do I fix Error Code E20 on my LG washer?",
        "answer": "Error E20 indicates a drain problem. Check the drain hose for clogs and ensure proper installation.",
        "keywords": ["E20", "LG", "drain", "error code"],
        "supported_models": ["LG WM3900", "LG WM4000"],
        "safety_level": "caution",
        "complexity_score": 4
    }
    
    create_response = client.post("/qa/entries", json=entry_data)
    assert create_response.status_code == 201
    created_entry = create_response.json()["data"]
    entry_id = created_entry["id"]
    
    # 2. Search for the entry
    search_response = client.post("/qa/search", json={
        "query": "E20 error LG drain",
        "max_results": 10
    })
    assert search_response.status_code == 200
    search_results = search_response.json()["data"]["results"]
    
    # Should find our created entry
    found_entry = None
    for result in search_results:
        if result["entry"]["id"] == entry_id:
            found_entry = result
            break
    
    assert found_entry is not None
    assert found_entry["entry"]["question"] == entry_data["question"]
    
    # 3. Get entry by ID
    get_response = client.get(f"/qa/entries/{entry_id}")
    assert get_response.status_code == 200
    retrieved_entry = get_response.json()["data"]
    assert retrieved_entry["id"] == entry_id
    
    # 4. Update the entry
    update_data = {
        "answer": "Error E20 indicates a drain problem. First, check the drain hose for clogs. Then ensure proper installation height.",
        "complexity_score": 5
    }
    
    update_response = client.put(f"/qa/entries/{entry_id}", json=update_data)
    assert update_response.status_code == 200
    updated_entry = update_response.json()["data"]
    assert updated_entry["answer"] == update_data["answer"]
    assert updated_entry["complexity_score"] == update_data["complexity_score"]
    
    # 5. Search again to verify update
    search_response2 = client.post("/qa/search", json={
        "query": "E20 installation height",
        "max_results": 10
    })
    assert search_response2.status_code == 200
    
    # 6. Delete the entry
    delete_response = client.delete(f"/qa/entries/{entry_id}")
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["data"]["message"]
    
    # 7. Verify entry is no longer found in active searches
    search_response3 = client.post("/qa/search", json={
        "query": "E20 error",
        "max_results": 10
    })
    assert search_response3.status_code == 200
    final_results = search_response3.json()["data"]["results"]
    
    # Should not find the deleted entry in active results
    deleted_found = any(r["entry"]["id"] == entry_id for r in final_results)
    assert not deleted_found


def test_search_relevance_ordering(client: TestClient):
    """Test that search results are properly ordered by relevance."""
    
    # Create entries with different relevance to a search term
    entries = [
        {
            "question": "Why won't my washing machine drain water?",
            "answer": "Check the drain hose for clogs and blockages.",
            "keywords": ["drain", "water", "clogs", "hose"],
            "safety_level": "caution",
            "complexity_score": 3
        },
        {
            "question": "How to clean washing machine?", 
            "answer": "Use vinegar and run a cleaning cycle to maintain your machine.",
            "keywords": ["clean", "maintenance", "vinegar"],
            "safety_level": "safe",
            "complexity_score": 2
        },
        {
            "question": "Drain pump motor replacement guide",
            "answer": "Drain pump replacement requires electrical work and should be done by professionals.",
            "keywords": ["drain pump", "motor", "replacement", "electrical"],
            "safety_level": "professional", 
            "complexity_score": 8
        }
    ]
    
    created_ids = []
    for entry_data in entries:
        response = client.post("/qa/entries", json=entry_data)
        assert response.status_code == 201
        created_ids.append(response.json()["data"]["id"])
    
    # Search for "drain" - should prioritize more relevant entries
    search_response = client.post("/qa/search", json={
        "query": "drain water problem",
        "max_results": 10
    })
    
    assert search_response.status_code == 200
    results = search_response.json()["data"]["results"]
    
    # Should have results
    assert len(results) > 0
    
    # Results should be ordered by relevance score
    for i in range(len(results) - 1):
        current_score = results[i]["relevance_score"]
        next_score = results[i + 1]["relevance_score"]
        assert current_score >= next_score
    
    # Clean up
    for entry_id in created_ids:
        client.delete(f"/qa/entries/{entry_id}")


def test_safety_level_filtering(client: TestClient):
    """Test filtering by safety levels works correctly."""
    
    # Create entries with different safety levels
    entries = [
        {
            "question": "Basic cleaning procedure",
            "answer": "Wipe with damp cloth weekly.",
            "safety_level": "safe",
            "complexity_score": 1
        },
        {
            "question": "Drain hose maintenance", 
            "answer": "Check for leaks and clogs regularly.",
            "safety_level": "caution",
            "complexity_score": 3
        },
        {
            "question": "Motor replacement procedure",
            "answer": "Requires electrical expertise and professional tools.",
            "safety_level": "professional",
            "complexity_score": 9
        }
    ]
    
    created_ids = []
    for entry_data in entries:
        entry_data.update({
            "keywords": ["test", "safety", "filtering"],
            "supported_models": ["Test Model"]
        })
        response = client.post("/qa/entries", json=entry_data)
        assert response.status_code == 201
        created_ids.append(response.json()["data"]["id"])
    
    # Test filtering by safe level only
    safe_search = client.post("/qa/search", json={
        "query": "test",
        "safety_levels": ["safe"],
        "max_results": 10
    })
    
    assert safe_search.status_code == 200
    safe_results = safe_search.json()["data"]["results"]
    
    for result in safe_results:
        assert result["entry"]["safety_level"] == "safe"
    
    # Test filtering by multiple levels
    multi_search = client.post("/qa/search", json={
        "query": "test", 
        "safety_levels": ["safe", "caution"],
        "max_results": 10
    })
    
    assert multi_search.status_code == 200
    multi_results = multi_search.json()["data"]["results"]
    
    for result in multi_results:
        assert result["entry"]["safety_level"] in ["safe", "caution"]
    
    # Clean up
    for entry_id in created_ids:
        client.delete(f"/qa/entries/{entry_id}")


def test_performance_under_load(client: TestClient):
    """Test system performance with multiple concurrent requests."""
    
    # Create test entries
    test_entries = []
    for i in range(10):
        entry_data = {
            "question": f"Test question {i} about washing machine issues",
            "answer": f"Test answer {i} providing troubleshooting guidance for various problems.",
            "keywords": [f"test{i}", "performance", "load"],
            "supported_models": ["Test Model"],
            "safety_level": "safe",
            "complexity_score": 2
        }
        
        response = client.post("/qa/entries", json=entry_data)
        assert response.status_code == 201
        test_entries.append(response.json()["data"]["id"])
    
    # Perform multiple searches
    search_queries = [
        "test washing machine",
        "performance issues",
        "troubleshooting guidance", 
        "load testing problems",
        "machine test questions"
    ]
    
    for query in search_queries:
        response = client.post("/qa/search", json={
            "query": query,
            "max_results": 5
        })
        assert response.status_code == 200
        
        # Check response time is reasonable
        data = response.json()["data"]
        assert data["query_time_ms"] < 5000  # Under 5 seconds
    
    # Clean up
    for entry_id in test_entries:
        client.delete(f"/qa/entries/{entry_id}")


def test_content_validation_integration(client: TestClient):
    """Test that content validation is properly integrated."""
    
    # Test creating entry with professional-level content
    professional_entry = {
        "question": "How do I test motor continuity with a multimeter?",
        "answer": "Use a multimeter to check electrical continuity across motor terminals. This requires electrical expertise.",
        "keywords": ["motor", "multimeter", "electrical", "continuity"],
        "supported_models": ["Test Model"],
        "safety_level": "safe",  # Should be upgraded by validator
        "complexity_score": 5
    }
    
    response = client.post("/qa/entries", json=professional_entry)
    assert response.status_code == 201
    
    created_entry = response.json()["data"]
    # Safety level should be upgraded to professional
    assert created_entry["safety_level"] == "professional"
    
    # Clean up
    client.delete(f"/qa/entries/{created_entry['id']}")


def test_api_response_format_consistency(client: TestClient):
    """Test that all endpoints return consistent API response format."""
    
    # Test health endpoint
    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert "data" in health_data
    assert "error" in health_data
    
    # Test search endpoint  
    search_response = client.post("/qa/search", json={"query": "test"})
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert "data" in search_data
    assert "error" in search_data
    
    # Test management endpoints
    list_response = client.get("/qa/entries")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert "data" in list_data
    assert "error" in list_data