# Database Schema

```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table - Microsoft Teams user context and preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teams_user_id VARCHAR(255) UNIQUE NOT NULL,
    teams_tenant_id VARCHAR(255),
    skill_level VARCHAR(50) CHECK (skill_level IN ('novice', 'diy_enthusiast', 'renter')),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Query sessions - conversation context and tracking
CREATE TABLE query_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    initial_query TEXT NOT NULL,
    conversation_context JSONB DEFAULT '[]',
    search_strategy_used VARCHAR(50) CHECK (search_strategy_used IN ('fast_qa', 'semantic', 'hybrid')),
    total_response_time_ms INTEGER,
    resolution_status VARCHAR(50) CHECK (resolution_status IN ('resolved', 'escalated', 'abandoned', 'ongoing')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fast Q&A entries - curated troubleshooting solutions
CREATE TABLE qa_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT[], -- Array for fast keyword matching
    search_vector TSVECTOR, -- Full-text search optimization
    supported_models TEXT[],
    safety_level VARCHAR(50) CHECK (safety_level IN ('safe', 'caution', 'professional')) DEFAULT 'safe',
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10) DEFAULT 5,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Manual content - processed manufacturer documentation
CREATE TABLE manual_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer VARCHAR(100) NOT NULL,
    model_series VARCHAR(100) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) CHECK (content_type IN ('troubleshooting', 'maintenance', 'safety', 'warranty')),
    search_vector TSVECTOR,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    source_manual VARCHAR(255),
    page_reference VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Safety classifications - repair safety assessment rules
CREATE TABLE safety_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repair_type VARCHAR(255) NOT NULL,
    safety_level VARCHAR(50) CHECK (safety_level IN ('safe_diy', 'requires_tools', 'professional_only', 'dangerous')) NOT NULL,
    reasoning TEXT NOT NULL,
    required_tools TEXT[],
    skill_requirements TEXT[],
    warning_text TEXT,
    rule_pattern TEXT, -- Regex or keyword pattern for matching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Query responses - individual responses with full context
CREATE TABLE query_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES query_sessions(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    source_type VARCHAR(50) CHECK (source_type IN ('fast_qa', 'semantic_search', 'safety_override', 'knowledge_gap')) NOT NULL,
    source_id UUID, -- References qa_entries or manual_content
    safety_classification_id UUID REFERENCES safety_classifications(id),
    confidence_score DECIMAL(3,2),
    user_feedback VARCHAR(50) CHECK (user_feedback IN ('helpful', 'not_helpful', 'dangerous')),
    resolution_successful BOOLEAN,
    response_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization
CREATE INDEX idx_users_teams_id ON users(teams_user_id);
CREATE INDEX idx_qa_entries_search_vector ON qa_entries USING gin(search_vector);
CREATE INDEX idx_qa_entries_keywords ON qa_entries USING gin(keywords);
CREATE INDEX idx_manual_content_search_vector ON manual_content USING gin(search_vector);
CREATE INDEX idx_query_responses_created_at ON query_responses(created_at);
CREATE INDEX idx_query_responses_response_time ON query_responses(response_time_ms);

-- Create triggers for automatic search vector updates
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'qa_entries' THEN
        NEW.search_vector := to_tsvector('english', COALESCE(NEW.question, '') || ' ' || COALESCE(NEW.answer, '') || ' ' || array_to_string(COALESCE(NEW.keywords, ARRAY[]::TEXT[]), ' '));
    ELSIF TG_TABLE_NAME = 'manual_content' THEN
        NEW.search_vector := to_tsvector('english', COALESCE(NEW.section_title, '') || ' ' || COALESCE(NEW.content, ''));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER qa_entries_search_vector_update
    BEFORE INSERT OR UPDATE ON qa_entries
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

CREATE TRIGGER manual_content_search_vector_update
    BEFORE INSERT OR UPDATE ON manual_content
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```
