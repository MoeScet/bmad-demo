"""
Integration tests for database schema and migrations.
Tests require a running PostgreSQL instance.
"""
import asyncio
import os
from pathlib import Path

import pytest
import pytest_asyncio
import asyncpg


# Database configuration for tests
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/bmad_test"
)


@pytest_asyncio.fixture
async def db_connection():
    """Create test database connection."""
    try:
        conn = await asyncpg.connect(TEST_DATABASE_URL)
        yield conn
    except asyncpg.exceptions.CannotConnectNowError:
        pytest.skip("PostgreSQL not available for testing")
    finally:
        if 'conn' in locals():
            await conn.close()


@pytest_asyncio.fixture
async def clean_database(db_connection):
    """Clean database before and after tests."""
    # Clean before test
    await db_connection.execute("DROP SCHEMA IF EXISTS public CASCADE;")
    await db_connection.execute("CREATE SCHEMA public;")
    
    # Run migration
    migration_file = Path(__file__).parents[2] / "infrastructure" / "database" / "migrations" / "001_initial_schema.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    await db_connection.execute(migration_sql)
    
    yield db_connection
    
    # Clean after test
    await db_connection.execute("DROP SCHEMA IF EXISTS public CASCADE;")
    await db_connection.execute("CREATE SCHEMA public;")


class TestDatabaseSchema:
    """Test database schema and constraints."""
    
    @pytest.mark.asyncio
    async def test_extensions_installed(self, clean_database):
        """Test required PostgreSQL extensions are installed."""
        # Check uuid-ossp extension
        result = await clean_database.fetch(
            "SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp'"
        )
        assert len(result) == 1
        
        # Check pg_trgm extension
        result = await clean_database.fetch(
            "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'"
        )
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_tables_created(self, clean_database):
        """Test all required tables are created."""
        expected_tables = [
            'users', 'query_sessions', 'qa_entries', 'manual_content',
            'safety_classifications', 'query_responses'
        ]
        
        for table_name in expected_tables:
            result = await clean_database.fetch(
                "SELECT 1 FROM information_schema.tables WHERE table_name = $1",
                table_name
            )
            assert len(result) == 1, f"Table {table_name} not found"
    
    @pytest.mark.asyncio
    async def test_user_operations(self, clean_database):
        """Test user table operations."""
        # Insert test user
        user_id = await clean_database.fetchval("""
            INSERT INTO users (teams_user_id, teams_tenant_id, skill_level, preferences)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, "test-user-123", "test-tenant-456", "diy_enthusiast", {"theme": "dark"})
        
        assert user_id is not None
        
        # Fetch user
        user = await clean_database.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        
        assert user['teams_user_id'] == "test-user-123"
        assert user['skill_level'] == "diy_enthusiast"
        assert user['preferences'] == {"theme": "dark"}
    
    @pytest.mark.asyncio
    async def test_qa_entry_search_vector(self, clean_database):
        """Test automatic search vector generation for Q&A entries."""
        # Insert Q&A entry
        qa_id = await clean_database.fetchval("""
            INSERT INTO qa_entries (question, answer, keywords, safety_level)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, 
        "How do I fix washing machine drain?",
        "Check the drain hose for clogs and ensure proper installation.",
        ["drain", "clog", "hose"],
        "safe"
        )
        
        # Verify search vector was generated
        search_vector = await clean_database.fetchval(
            "SELECT search_vector FROM qa_entries WHERE id = $1", qa_id
        )
        
        assert search_vector is not None
        
        # Test search functionality
        results = await clean_database.fetch("""
            SELECT id, question FROM qa_entries 
            WHERE search_vector @@ plainto_tsquery('english', 'drain washing machine')
        """)
        
        assert len(results) == 1
        assert results[0]['id'] == qa_id
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, clean_database):
        """Test foreign key constraints are working."""
        # Create user first
        user_id = await clean_database.fetchval("""
            INSERT INTO users (teams_user_id) VALUES ($1) RETURNING id
        """, "test-user-fk")
        
        # Create query session
        session_id = await clean_database.fetchval("""
            INSERT INTO query_sessions (user_id, initial_query)
            VALUES ($1, $2) RETURNING id
        """, user_id, "Test query")
        
        # Create query response
        await clean_database.execute("""
            INSERT INTO query_responses 
            (session_id, query_text, response_text, source_type, response_time_ms)
            VALUES ($1, $2, $3, $4, $5)
        """, session_id, "test query", "test response", "fast_qa", 100)
        
        # Try to delete user (should fail due to cascade)
        # But first, verify the cascade works by deleting user
        await clean_database.execute("DELETE FROM users WHERE id = $1", user_id)
        
        # Verify session was cascaded deleted
        session_count = await clean_database.fetchval(
            "SELECT COUNT(*) FROM query_sessions WHERE user_id = $1", user_id
        )
        assert session_count == 0
        
        # Verify response was cascaded deleted
        response_count = await clean_database.fetchval(
            "SELECT COUNT(*) FROM query_responses WHERE session_id = $1", session_id
        )
        assert response_count == 0