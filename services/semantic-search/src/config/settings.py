"""
Semantic Search Service Configuration

Service-specific configuration that extends the base configuration
with vector database and embedding model settings.
"""

from shared.python.config.base import VectorDatabaseConfig


class SemanticSearchConfig(VectorDatabaseConfig):
    """Configuration for semantic search service"""

    # Service-specific overrides
    SERVICE_NAME: str = "semantic-search"

    # Collection configuration
    DEFAULT_COLLECTION: str = "manual_content_embeddings"
    ENSURE_COLLECTION_EXISTS: bool = True

    # Search configuration
    DEFAULT_SEARCH_RESULTS: int = 10
    MAX_SEARCH_RESULTS: int = 50


def get_settings() -> SemanticSearchConfig:
    """Get semantic search service configuration"""
    return SemanticSearchConfig()