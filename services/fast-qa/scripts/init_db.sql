-- Fast Q&A Database Initialization Script
-- Creates necessary PostgreSQL extensions and configurations

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search extensions  
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create indexes for better performance (these will be created by SQLAlchemy migrations too)
-- This script ensures they exist even without migrations

-- Grant permissions to fastqa_user
GRANT ALL PRIVILEGES ON DATABASE fastqa_db TO fastqa_user;
GRANT ALL ON SCHEMA public TO fastqa_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fastqa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fastqa_user;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fastqa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fastqa_user;