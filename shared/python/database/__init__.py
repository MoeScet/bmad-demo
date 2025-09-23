"""
Database utilities and clients for BMAD services.

Provides shared database access patterns, connection management,
and vector database operations.
"""

from .vector_client import ChromaDBClient, VectorDatabaseError, get_vector_client

__all__ = [
    "ChromaDBClient",
    "VectorDatabaseError",
    "get_vector_client",
]