"""
Tests for Q&A management (CRUD) endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from models.qa_entry import QAEntry


def test_create_qa_entry(client: TestClient):
    """Test creating a new Q&A entry."""
    entry_data = {
        "question": "How do I clean my washing machine filter?",
        "answer": "Remove the filter from the bottom front of the machine and rinse under hot water.",
        "keywords": ["clean", "filter", "rinse"],
        "supported_models": ["LG WM3900", "Samsung WF45"],
        "safety_level": "safe",
        "complexity_score": 3
    }
    
    response = client.post("/qa/entries", json=entry_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["error"] is None
    entry = data["data"]
    assert entry["question"] == entry_data["question"]
    assert entry["answer"] == entry_data["answer"]
    assert entry["keywords"] == entry_data["keywords"]
    assert entry["safety_level"] == entry_data["safety_level"]
    assert "id" in entry
    assert "created_at" in entry


def test_create_qa_entry_with_validation(client: TestClient):
    """Test creating entry with content validation."""
    entry_data = {
        "question": "How do I replace the motor?",
        "answer": "This requires electrical work with voltage testing. Contact a qualified technician.",
        "keywords": ["motor", "electrical", "voltage"],
        "supported_models": ["GE GTW"],
        "safety_level": "safe",  # Should be upgraded by validator
        "complexity_score": 5
    }
    
    response = client.post("/qa/entries", json=entry_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Safety level should be upgraded to professional due to electrical content
    entry = data["data"]
    assert entry["safety_level"] == "professional"


def test_create_qa_entry_invalid_data(client: TestClient):
    """Test creating entry with invalid data."""
    entry_data = {
        "question": "Too short",  # Should fail validation
        "answer": "Too short",    # Should fail validation
        "safety_level": "invalid_level",
        "complexity_score": 15    # Out of range
    }
    
    response = client.post("/qa/entries", json=entry_data)
    
    assert response.status_code == 422  # Validation error


def test_list_qa_entries(client: TestClient, multiple_qa_entries):
    """Test listing Q&A entries with pagination."""
    response = client.get("/qa/entries?page=1&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    list_data = data["data"]
    assert "entries" in list_data
    assert "total_count" in list_data
    assert "page" in list_data
    assert "page_size" in list_data
    assert "total_pages" in list_data
    
    assert len(list_data["entries"]) <= 2
    assert list_data["page"] == 1
    assert list_data["page_size"] == 2


def test_list_qa_entries_active_only(client: TestClient, multiple_qa_entries):
    """Test listing only active entries."""
    response = client.get("/qa/entries?active_only=true")
    
    assert response.status_code == 200
    data = response.json()
    
    entries = data["data"]["entries"]
    for entry in entries:
        assert entry["is_active"] is True


def test_get_qa_entry_by_id_management(client: TestClient, sample_qa_entry):
    """Test getting a specific entry through management endpoint."""
    response = client.get(f"/qa/entries/{sample_qa_entry.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    entry = data["data"]
    assert entry["id"] == str(sample_qa_entry.id)
    assert entry["question"] == sample_qa_entry.question


def test_get_qa_entry_not_found_management(client: TestClient):
    """Test getting non-existent entry through management endpoint."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/qa/entries/{fake_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"] is None
    assert data["error"]["code"] == "ENTRY_NOT_FOUND"


def test_update_qa_entry(client: TestClient, sample_qa_entry):
    """Test updating an existing Q&A entry."""
    update_data = {
        "answer": "Updated answer with more detailed instructions.",
        "complexity_score": 4
    }
    
    response = client.put(f"/qa/entries/{sample_qa_entry.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    entry = data["data"]
    assert entry["answer"] == update_data["answer"]
    assert entry["complexity_score"] == update_data["complexity_score"]
    assert entry["question"] == sample_qa_entry.question  # Unchanged


def test_update_qa_entry_not_found(client: TestClient):
    """Test updating non-existent entry."""
    fake_id = str(uuid.uuid4())
    update_data = {"answer": "Updated answer"}
    
    response = client.put(f"/qa/entries/{fake_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"] is None
    assert data["error"]["code"] == "ENTRY_NOT_FOUND"


def test_delete_qa_entry(client: TestClient, sample_qa_entry):
    """Test soft deleting a Q&A entry."""
    response = client.delete(f"/qa/entries/{sample_qa_entry.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["error"] is None
    assert "deleted successfully" in data["data"]["message"]
    assert data["data"]["entry_id"] == str(sample_qa_entry.id)


def test_delete_qa_entry_not_found(client: TestClient):
    """Test deleting non-existent entry."""
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/qa/entries/{fake_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"] is None
    assert data["error"]["code"] == "ENTRY_NOT_FOUND"


def test_create_entry_with_correlation_id(client: TestClient):
    """Test creating entry with correlation ID."""
    entry_data = {
        "question": "Test question with correlation ID",
        "answer": "Test answer for correlation ID testing purposes.",
        "keywords": ["test", "correlation"],
        "safety_level": "safe",
        "complexity_score": 1
    }
    
    correlation_id = str(uuid.uuid4())
    response = client.post("/qa/entries", 
        json=entry_data,
        headers={"X-Correlation-ID": correlation_id}
    )
    
    assert response.status_code == 201
    # Correlation ID should be used for logging but doesn't affect response


def test_list_entries_pagination(client: TestClient, multiple_qa_entries):
    """Test pagination functionality."""
    # Get first page
    response1 = client.get("/qa/entries?page=1&page_size=2")
    assert response1.status_code == 200
    data1 = response1.json()["data"]
    
    # Get second page
    response2 = client.get("/qa/entries?page=2&page_size=2")
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    
    # Should have different entries on different pages
    if len(data1["entries"]) > 0 and len(data2["entries"]) > 0:
        entry1_ids = {entry["id"] for entry in data1["entries"]}
        entry2_ids = {entry["id"] for entry in data2["entries"]}
        assert not entry1_ids.intersection(entry2_ids)  # No overlap


def test_create_entry_exceeds_keyword_limit(client: TestClient):
    """Test creating entry with too many keywords."""
    entry_data = {
        "question": "Test question with too many keywords",
        "answer": "Test answer for keyword validation.",
        "keywords": [f"keyword{i}" for i in range(25)],  # Exceeds 20 keyword limit
        "safety_level": "safe",
        "complexity_score": 1
    }
    
    response = client.post("/qa/entries", json=entry_data)
    
    assert response.status_code == 422  # Should fail validation