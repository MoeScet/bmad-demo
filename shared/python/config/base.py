"""
Base configuration management for BMAD services.
Implements secure environment variable loading with validation.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration class with common settings for all services."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",
    )
    
    # Environment Settings
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production|test)$")
    SERVICE_NAME: str = Field(..., description="Service identifier")
    SERVICE_VERSION: str = Field("1.0.0", description="Service version")
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", pattern="^(DEBUG|INFO|WARN|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field("json", pattern="^(json|text)$")
    CORRELATION_ID_HEADER: str = Field("X-Correlation-ID")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_SIZE: int = Field(10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(20, ge=0, le=100)
    DATABASE_POOL_TIMEOUT: int = Field(30, ge=1, le=300)
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: float = Field(30.0, ge=0.1, le=300.0)
    HTTP_MAX_RETRIES: int = Field(3, ge=0, le=10)
    HTTP_BACKOFF_FACTOR: float = Field(0.3, ge=0.0, le=5.0)
    
    # Security Configuration
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["*"])
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    
    # Monitoring and Observability
    ENABLE_METRICS: bool = Field(True)
    METRICS_PORT: int = Field(8000, ge=1024, le=65535)
    HEALTH_CHECK_TIMEOUT: float = Field(5.0, ge=0.1, le=60.0)
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate PostgreSQL connection string format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string")
        return v
    
    @field_validator("SERVICE_NAME")
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        """Ensure service name follows kebab-case convention."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("SERVICE_NAME must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracking."""
        return str(uuid.uuid4())
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT == "test"


class TeamsConfig(BaseConfig):
    """Configuration specific to Microsoft Teams integration."""
    
    # Microsoft Teams Bot Framework
    TEAMS_BOT_APP_ID: str = Field(..., description="Microsoft Teams Bot Application ID")
    TEAMS_BOT_APP_PASSWORD: str = Field(..., description="Microsoft Teams Bot Application Password")
    TEAMS_BOT_TENANT_ID: str = Field(..., description="Microsoft Teams Tenant ID")
    
    # Teams Bot Settings
    TEAMS_BOT_TIMEOUT: float = Field(30.0, ge=1.0, le=300.0)
    TEAMS_BOT_MAX_CONVERSATION_MEMBERS: int = Field(100, ge=1, le=1000)
    
    @field_validator("TEAMS_BOT_APP_ID")
    @classmethod
    def validate_teams_app_id(cls, v: str) -> str:
        """Validate Teams App ID format (UUID)."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("TEAMS_BOT_APP_ID must be a valid UUID")
        return v


class ServiceTimeoutConfig(BaseConfig):
    """Timeout configuration for service-to-service communication."""
    
    # Service-specific timeouts (in seconds)
    FAST_QA_TIMEOUT: float = Field(3.0, ge=0.1, le=60.0, description="Fast Q&A service timeout")
    SEMANTIC_SEARCH_TIMEOUT: float = Field(12.0, ge=0.1, le=60.0, description="Semantic search timeout") 
    SAFETY_CLASSIFICATION_TIMEOUT: float = Field(1.0, ge=0.1, le=30.0, description="Safety classification timeout")
    USER_CONTEXT_TIMEOUT: float = Field(0.5, ge=0.1, le=10.0, description="User context timeout")
    
    # Query orchestration settings
    QUERY_ORCHESTRATION_MAX_PARALLEL: int = Field(5, ge=1, le=20)
    QUERY_ORCHESTRATION_CIRCUIT_BREAKER_THRESHOLD: int = Field(5, ge=1, le=100)


class VectorDatabaseConfig(BaseConfig):
    """Configuration for ChromaDB vector database operations."""
    
    # ChromaDB Settings
    CHROMA_HOST: str = Field("localhost", description="ChromaDB host")
    CHROMA_PORT: int = Field(8000, ge=1024, le=65535, description="ChromaDB port")
    CHROMA_COLLECTION_NAME: str = Field("bmad_embeddings", description="ChromaDB collection name")
    
    # Embedding Settings
    EMBEDDING_MODEL: str = Field("sentence-transformers/all-MiniLM-L6-v2", description="Sentence transformer model")
    EMBEDDING_DIMENSION: int = Field(384, ge=1, le=4096, description="Embedding vector dimension")
    MAX_EMBEDDING_BATCH_SIZE: int = Field(32, ge=1, le=1000, description="Max batch size for embeddings")
    
    # Search Settings
    SIMILARITY_THRESHOLD: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    MAX_SEARCH_RESULTS: int = Field(10, ge=1, le=100, description="Maximum search results to return")


def load_config(config_class: type[BaseConfig] = BaseConfig) -> BaseConfig:
    """
    Load configuration with environment-specific overrides.

    Args:
        config_class: Configuration class to instantiate

    Returns:
        Configured instance

    Raises:
        ValueError: If configuration validation fails
    """
    return config_class()


def get_settings() -> VectorDatabaseConfig:
    """Get vector database configuration settings."""
    return VectorDatabaseConfig()