"""
Configuration settings for Manual Processing Service
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration settings"""

    # Service configuration
    ENVIRONMENT: str = "development"
    PORT: int = 8005
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/bmad_dev"
    )

    # ChromaDB configuration
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_BASE_URL: str = f"http://{CHROMADB_HOST}:{CHROMADB_PORT}/api/v1"

    # Processing configuration
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf"]
    UPLOAD_DIRECTORY: str = "/tmp/manual-uploads"
    PROCESSING_TIMEOUT_SECONDS: int = 300  # 5 minutes

    # Embedding configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    MAX_CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Quality thresholds
    MIN_READABILITY_SCORE: float = 0.3
    MIN_TEXT_LENGTH: int = 50
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.9

    # ChromaDB collection names
    MANUAL_CONTENT_COLLECTION: str = "manual_content"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get service settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings