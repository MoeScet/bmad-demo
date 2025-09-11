"""
Pydantic models for Fast Q&A API validation and serialization.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class QASearchRequest(BaseModel):
    """Request model for Q&A search operations."""
    
    query: str = Field(..., min_length=3, max_length=500, description="Search query text")
    max_results: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum results to return")
    min_score: Optional[float] = Field(default=0.1, ge=0.0, le=1.0, description="Minimum relevance score")
    safety_levels: Optional[List[str]] = Field(
        default=None, 
        description="Filter by safety levels"
    )
    
    @validator('safety_levels')
    def validate_safety_levels(cls, v):
        if v is not None:
            allowed_levels = {'safe', 'caution', 'professional'}
            for level in v:
                if level not in allowed_levels:
                    raise ValueError(f"Invalid safety level: {level}. Must be one of {allowed_levels}")
        return v


class QAEntryResponse(BaseModel):
    """Response model for Q&A entry data."""
    
    id: uuid.UUID
    question: str
    answer: str
    keywords: Optional[List[str]] = None
    supported_models: Optional[List[str]] = None
    safety_level: str
    complexity_score: int
    success_rate: float
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QASearchResult(BaseModel):
    """Individual search result with relevance scoring."""
    
    entry: QAEntryResponse
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")
    match_type: str = Field(..., description="Type of match (keyword, full_text, etc.)")


class QASearchResponse(BaseModel):
    """Response model for search operations."""
    
    results: List[QASearchResult]
    total_count: int = Field(..., ge=0, description="Total number of matching entries")
    query_time_ms: int = Field(..., ge=0, description="Query execution time in milliseconds")
    applied_filters: dict = Field(..., description="Filters applied to search")


class QAEntryCreate(BaseModel):
    """Model for creating new Q&A entries."""
    
    question: str = Field(..., min_length=10, max_length=1000, description="Question text")
    answer: str = Field(..., min_length=20, max_length=5000, description="Answer text")
    keywords: Optional[List[str]] = Field(default=None, description="Search keywords")
    supported_models: Optional[List[str]] = Field(default=None, description="Supported washing machine models")
    safety_level: str = Field(default="safe", description="Safety classification")
    complexity_score: int = Field(default=5, ge=1, le=10, description="Complexity rating (1-10)")
    
    @validator('safety_level')
    def validate_safety_level(cls, v):
        allowed_levels = {'safe', 'caution', 'professional'}
        if v not in allowed_levels:
            raise ValueError(f"Invalid safety level: {v}. Must be one of {allowed_levels}")
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")
        return v


class QAEntryUpdate(BaseModel):
    """Model for updating existing Q&A entries."""
    
    question: Optional[str] = Field(None, min_length=10, max_length=1000)
    answer: Optional[str] = Field(None, min_length=20, max_length=5000)
    keywords: Optional[List[str]] = None
    supported_models: Optional[List[str]] = None
    safety_level: Optional[str] = None
    complexity_score: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None
    
    @validator('safety_level')
    def validate_safety_level(cls, v):
        if v is not None:
            allowed_levels = {'safe', 'caution', 'professional'}
            if v not in allowed_levels:
                raise ValueError(f"Invalid safety level: {v}. Must be one of {allowed_levels}")
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")
        return v


class QAEntryListResponse(BaseModel):
    """Response model for paginated Q&A entry listings."""
    
    entries: List[QAEntryResponse]
    total_count: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=0)


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    
    data: Optional[dict] = None
    error: Optional[dict] = None