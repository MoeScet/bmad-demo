# Fast Q&A Service API Documentation

## Service Information
- **Service Name:** Fast Q&A Service
- **Version:** 1.3.0
- **Base URL:** `http://localhost:8003` (development)
- **Interactive Docs:** `http://localhost:8003/docs`

## Environment Configuration
```bash
# Development (SQLite)
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8003
FAST_QA_DATABASE_URL=sqlite+aiosqlite:///./fastqa_test.db

# Production (PostgreSQL)  
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8003
FAST_QA_DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```

## Authentication
Currently no authentication required for development. Production should implement proper authentication for management endpoints.

## API Endpoints

### Health Endpoints

#### Get Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "service": "fast-qa",
    "version": "1.3.0"
  },
  "error": null
}
```

#### Get Detailed Health Check
```http
GET /health/detailed
```

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "service": "fast-qa", 
    "version": "1.3.0",
    "database": "connected",
    "environment": "development"
  },
  "error": null
}
```

### Q&A Management Endpoints

#### List Q&A Entries
```http
GET /qa/entries?page=1&page_size=10&active_only=true
```

**Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)
- `active_only` (boolean): Filter active entries only (default: true)

**Response:**
```json
{
  "data": {
    "entries": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "question": "Why won't my washing machine start?",
        "answer": "Check if the machine is plugged in, door is closed, and water supply is on.",
        "keywords": ["start", "power", "door", "water"],
        "supported_models": ["LG WM3900", "Samsung WF45"],
        "safety_level": "safe",
        "complexity_score": 2,
        "success_rate": 0.85,
        "usage_count": 42,
        "is_active": true,
        "created_at": "2025-09-11T08:20:04",
        "updated_at": "2025-09-11T08:20:04"
      }
    ],
    "total_count": 15,
    "page": 1,
    "page_size": 10,
    "total_pages": 2
  },
  "error": null
}
```

#### Get Specific Q&A Entry
```http
GET /qa/entries/{entry_id}
```

**Response:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Why won't my washing machine start?",
    "answer": "Check if the machine is plugged in, door is closed, and water supply is on.",
    "keywords": ["start", "power", "door", "water"],
    "supported_models": ["LG WM3900", "Samsung WF45"],
    "safety_level": "safe",
    "complexity_score": 2,
    "success_rate": 0.85,
    "usage_count": 42,
    "is_active": true,
    "created_at": "2025-09-11T08:20:04",
    "updated_at": "2025-09-11T08:20:04"
  },
  "error": null
}
```

#### Create New Q&A Entry
```http
POST /qa/entries
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "Why won't my washing machine drain water?",
  "answer": "Check the drain hose for clogs and ensure proper installation.",
  "keywords": ["drain", "water", "clogs", "hose"],
  "supported_models": ["LG WM3900", "Samsung WF45"],
  "safety_level": "caution",
  "complexity_score": 4
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "question": "Why won't my washing machine drain water?",
    "answer": "Check the drain hose for clogs and ensure proper installation.",
    "keywords": ["drain", "water", "clogs", "hose"],
    "supported_models": ["LG WM3900", "Samsung WF45"],
    "safety_level": "caution",
    "complexity_score": 4,
    "success_rate": 0.0,
    "usage_count": 0,
    "is_active": true,
    "created_at": "2025-09-11T08:25:30",
    "updated_at": "2025-09-11T08:25:30"
  },
  "error": null
}
```

#### Update Q&A Entry
```http
PUT /qa/entries/{entry_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "answer": "Updated answer with more detailed steps...",
  "complexity_score": 3
}
```

**Response:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "question": "Why won't my washing machine drain water?",
    "answer": "Updated answer with more detailed steps...",
    "keywords": ["drain", "water", "clogs", "hose"],
    "supported_models": ["LG WM3900", "Samsung WF45"],
    "safety_level": "caution",
    "complexity_score": 3,
    "success_rate": 0.0,
    "usage_count": 0,
    "is_active": true,
    "created_at": "2025-09-11T08:25:30",
    "updated_at": "2025-09-11T08:30:15"
  },
  "error": null
}
```

#### Delete Q&A Entry
```http
DELETE /qa/entries/{entry_id}
```

**Response (204 No Content):**
```json
{
  "data": {
    "message": "Q&A entry deleted successfully",
    "entry_id": "550e8400-e29b-41d4-a716-446655440001"
  },
  "error": null
}
```

### Search Endpoints

#### Search Q&A Entries
```http
POST /qa/search
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "washing machine won't start power issue",
  "max_results": 10,
  "safety_levels": ["safe", "caution"],
  "supported_models": ["LG WM3900"]
}
```

**Response:**
```json
{
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "question": "Why won't my washing machine start?",
        "answer": "Check if the machine is plugged in, door is closed, and water supply is on.",
        "keywords": ["start", "power", "door", "water"],
        "supported_models": ["LG WM3900", "Samsung WF45"],
        "safety_level": "safe",
        "complexity_score": 2,
        "success_rate": 0.85,
        "usage_count": 42,
        "relevance_score": 0.95
      }
    ],
    "query": "washing machine won't start power issue",
    "total_results": 1,
    "search_time_ms": 23
  },
  "error": null
}
```

**Note:** Search functionality requires PostgreSQL for full-text search features. SQLite implementation has limited search capabilities.

#### Get Q&A Entry (Alternative Route)
```http
GET /qa/entry/{entry_id}
```

Same response format as `GET /qa/entries/{entry_id}`.

## Data Models

### QA Entry Fields
- `id` (string): Unique identifier (UUID format in production)
- `question` (string, required): The question text
- `answer` (string, required): The answer text
- `keywords` (array of strings): Keywords for search optimization
- `supported_models` (array of strings): Compatible washing machine models
- `safety_level` (string): One of "safe", "caution", "professional"
- `complexity_score` (integer): Difficulty rating from 1-10
- `success_rate` (float): User success rate (0.0-1.0)
- `usage_count` (integer): How many times this entry was accessed
- `is_active` (boolean): Whether the entry is active
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last modification timestamp

### Safety Levels
- **safe**: Basic maintenance that any user can perform
- **caution**: Requires some technical knowledge and safety precautions
- **professional**: Should only be performed by qualified technicians

## Error Responses

### Standard Error Format
```json
{
  "data": null,
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE",
    "details": {}
  }
}
```

### Common Error Codes
- `ENTRY_NOT_FOUND`: Q&A entry does not exist
- `VALIDATION_ERROR`: Request data validation failed
- `CREATE_ENTRY_ERROR`: Failed to create new entry
- `UPDATE_ENTRY_ERROR`: Failed to update entry
- `DELETE_ENTRY_ERROR`: Failed to delete entry
- `SEARCH_ERROR`: Search operation failed
- `DATABASE_ERROR`: Database connection or query error

## Rate Limiting
Currently no rate limiting implemented. Production should implement appropriate rate limiting.

## CORS Configuration
Development allows all origins (`*`). Production should restrict to specific domains.

## Database Compatibility

### Development (SQLite)
- ✅ All CRUD operations
- ✅ Basic filtering and pagination
- ❌ Advanced full-text search
- ❌ Complex queries with arrays

### Production (PostgreSQL)  
- ✅ All CRUD operations
- ✅ Advanced full-text search with TSVECTOR
- ✅ GIN indexes for performance
- ✅ Array operations and complex queries

## Example Usage

### Create and Search Workflow
```bash
# 1. Create a new Q&A entry
curl -X POST "http://localhost:8003/qa/entries" \
    -H "Content-Type: application/json" \
    -d '{
      "question": "Washing machine makes loud noise during spin cycle",
      "answer": "Check for unbalanced load or worn bearings. Redistribute clothes evenly.",
      "keywords": ["noise", "spin", "loud", "bearings", "unbalanced"],
      "supported_models": ["Whirlpool WTW5000"],
      "safety_level": "caution",
      "complexity_score": 6
    }'

# 2. List all entries
curl "http://localhost:8003/qa/entries?page=1&page_size=5"

# 3. Search for entries (PostgreSQL only for full functionality)
curl -X POST "http://localhost:8003/qa/search" \
    -H "Content-Type: application/json" \
    -d '{
      "query": "loud noise spin cycle",
      "max_results": 5
    }'
```

## Development Setup

### Running the Service
```bash
# Using Python directly
"/c/Users/moesc/anaconda3/envs/fast-qa/python.exe" src/main.py

# Using uvicorn (recommended)
"/c/Users/moesc/anaconda3/envs/fast-qa/Scripts/uvicorn.exe" src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Initialize Database
```bash
# SQLite
"/c/Users/moesc/anaconda3/envs/fast-qa/python.exe" scripts/init_sqlite_db.py
```

### Run Tests
```bash
"/c/Users/moesc/anaconda3/envs/fast-qa/Scripts/pytest.exe" tests/ -v
```