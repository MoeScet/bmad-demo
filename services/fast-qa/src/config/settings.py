"""
Fast Q&A Service Configuration
Environment configuration for Fast Q&A service with database and timeout settings.
"""
from __future__ import annotations

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class FastQAConfig(BaseSettings):
    """Fast Q&A Service Configuration with database and performance settings."""

    # Service Information
    SERVICE_NAME: str = "fast-qa"
    SERVICE_VERSION: str = "1.3.0"
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Logging format")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8003, description="Server port")

    # CORS Configuration
    CORS_ORIGINS: Optional[str] = Field(default=None, description="CORS allowed origins (comma-separated)")
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Database Configuration
    FAST_QA_DATABASE_URL: str = Field(description="PostgreSQL database connection URL")

    # Performance Configuration
    FAST_QA_TIMEOUT: float = Field(default=3.0, description="Fast Q&A operation timeout in seconds")
    FAST_QA_MAX_RESULTS: int = Field(default=10, description="Maximum search results to return")
    FAST_QA_MIN_SCORE: float = Field(default=0.1, description="Minimum relevance score threshold")
    
    # ML Ranking Configuration
    FAST_QA_ML_RANKING_ENABLED: bool = Field(default=True, description="Enable ML-based search ranking")
    FAST_QA_ML_RANKING_WEIGHT: float = Field(default=0.6, description="Weight for ML score vs keyword relevance")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Global configuration instance
fast_qa_config = FastQAConfig()