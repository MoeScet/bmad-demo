"""
Q&A content management API endpoints for CRUD operations.
"""
from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.database import get_database_session
from models.schemas import (
    QAEntryCreate, QAEntryUpdate, QAEntryResponse, 
    QAEntryListResponse, APIResponse
)
from repositories.qa_repository import QARepository

router = APIRouter()
logger = structlog.get_logger(__name__)


async def get_qa_repository(
    session: AsyncSession = Depends(get_database_session)
) -> QARepository:
    """Dependency to get QA repository instance."""
    return QARepository(session)


@router.get("/entries", response_model=APIResponse)
async def list_qa_entries(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(default=True, description="Filter active entries only"),
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    List Q&A entries with pagination.
    
    Supports filtering by active status and pagination controls.
    """
    try:
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A entries list request",
            correlation_id=correlation_id,
            service="fast-qa",
            page=page,
            page_size=page_size,
            active_only=active_only
        )
        
        entries, total_count = await qa_repo.list_entries(
            page=page,
            page_size=page_size,
            active_only=active_only
        )
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        # Convert entries to response format
        entry_responses = [QAEntryResponse.from_orm(entry) for entry in entries]
        
        list_response = QAEntryListResponse(
            entries=entry_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
        logger.info(
            "Q&A entries listed successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            entries_returned=len(entries),
            total_count=total_count
        )
        
        return {
            "data": list_response.dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to list Q&A entries",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e),
            page=page,
            page_size=page_size
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to list Q&A entries",
                "code": "LIST_ENTRIES_ERROR"
            }
        )


@router.post("/entries", response_model=APIResponse, status_code=201)
async def create_qa_entry(
    entry_data: QAEntryCreate,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Create a new Q&A entry.
    
    Validates input data and creates entry with search optimization.
    """
    try:
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A entry creation request",
            correlation_id=correlation_id,
            service="fast-qa",
            safety_level=entry_data.safety_level,
            complexity_score=entry_data.complexity_score
        )
        
        # Create the entry
        new_entry = await qa_repo.create_entry(entry_data)
        
        logger.info(
            "Q&A entry created successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(new_entry.id),
            safety_level=new_entry.safety_level
        )
        
        return {
            "data": QAEntryResponse.from_orm(new_entry).dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to create Q&A entry",
            correlation_id=x_correlation_id,
            service="fast-qa",
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to create Q&A entry",
                "code": "CREATE_ENTRY_ERROR"
            }
        )


@router.get("/entries/{entry_id}", response_model=APIResponse)
async def get_qa_entry_by_id(
    entry_id: str,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """Get a specific Q&A entry by ID."""
    try:
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A entry get request",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        entry = await qa_repo.get_entry_by_id(entry_id)
        
        if not entry:
            return {
                "data": None,
                "error": {
                    "message": "Q&A entry not found",
                    "code": "ENTRY_NOT_FOUND",
                    "entry_id": str(entry_id)
                }
            }
        
        logger.info(
            "Q&A entry retrieved successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        return {
            "data": QAEntryResponse.from_orm(entry).dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to get Q&A entry",
            correlation_id=x_correlation_id,
            service="fast-qa",
            entry_id=str(entry_id),
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve Q&A entry",
                "code": "GET_ENTRY_ERROR"
            }
        )


@router.put("/entries/{entry_id}", response_model=APIResponse)
async def update_qa_entry(
    entry_id: str,
    entry_data: QAEntryUpdate,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Update an existing Q&A entry.
    
    Supports partial updates and maintains search optimization.
    """
    try:
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A entry update request",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        # Update the entry
        updated_entry = await qa_repo.update_entry(entry_id, entry_data)
        
        if not updated_entry:
            return {
                "data": None,
                "error": {
                    "message": "Q&A entry not found",
                    "code": "ENTRY_NOT_FOUND",
                    "entry_id": str(entry_id)
                }
            }
        
        logger.info(
            "Q&A entry updated successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        return {
            "data": QAEntryResponse.from_orm(updated_entry).dict(),
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to update Q&A entry",
            correlation_id=x_correlation_id,
            service="fast-qa",
            entry_id=str(entry_id),
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to update Q&A entry",
                "code": "UPDATE_ENTRY_ERROR"
            }
        )


@router.delete("/entries/{entry_id}", response_model=APIResponse)
async def delete_qa_entry(
    entry_id: str,
    qa_repo: QARepository = Depends(get_qa_repository),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Soft delete a Q&A entry by setting is_active to False.
    
    Preserves data for audit trails while removing from active queries.
    """
    try:
        correlation_id = x_correlation_id or str(uuid.uuid4())
        
        logger.info(
            "Q&A entry delete request",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        # Perform soft delete
        success = await qa_repo.delete_entry(entry_id)
        
        if not success:
            return {
                "data": None,
                "error": {
                    "message": "Q&A entry not found",
                    "code": "ENTRY_NOT_FOUND",
                    "entry_id": str(entry_id)
                }
            }
        
        logger.info(
            "Q&A entry deleted successfully",
            correlation_id=correlation_id,
            service="fast-qa",
            entry_id=str(entry_id)
        )
        
        return {
            "data": {
                "message": "Q&A entry deleted successfully",
                "entry_id": str(entry_id)
            },
            "error": None
        }
        
    except Exception as e:
        logger.error(
            "Failed to delete Q&A entry",
            correlation_id=x_correlation_id,
            service="fast-qa",
            entry_id=str(entry_id),
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to delete Q&A entry",
                "code": "DELETE_ENTRY_ERROR"
            }
        )