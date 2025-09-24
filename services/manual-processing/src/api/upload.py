"""
File upload API endpoints for manual processing
"""

import os
import uuid
import logging
from typing import Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from ..config.settings import get_settings
from ..processing.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    job_id: str
    filename: str
    file_size: int
    status: str
    message: str


class ProcessingStatus(BaseModel):
    """Processing status response model"""
    job_id: str
    status: str  # queued, processing, completed, failed
    filename: str
    progress_percent: float
    message: str
    created_at: str
    completed_at: str = None
    error_details: str = None


@router.post("/upload", response_model=UploadResponse)
async def upload_manual(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Upload a PDF manual for processing
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    settings = get_settings()

    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Only PDF files are supported",
                    "correlation_id": correlation_id
                }
            )

        # Validate file size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
                    "correlation_id": correlation_id
                }
            )

        if file_size < 1024:  # Less than 1KB
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "File appears to be empty or corrupted",
                    "correlation_id": correlation_id
                }
            )

        # Generate job ID and save file
        job_id = str(uuid.uuid4())
        upload_dir = Path(settings.UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{job_id}_{file.filename}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(
            f"File uploaded successfully: {file.filename} ({file_size} bytes)",
            extra={'correlation_id': correlation_id, 'job_id': job_id}
        )

        # Start background processing
        processor = PDFProcessor()
        background_tasks.add_task(
            processor.process_pdf_file,
            str(file_path),
            job_id,
            correlation_id
        )

        return {
            "data": UploadResponse(
                job_id=job_id,
                filename=file.filename,
                file_size=file_size,
                status="queued",
                message="File uploaded successfully and queued for processing"
            ),
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Upload failed: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "File upload failed",
                "correlation_id": correlation_id
            }
        )


@router.get("/status/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(
    job_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Get processing status for a job
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))

    try:
        processor = PDFProcessor()
        status = await processor.get_job_status(job_id)

        if not status:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Job not found",
                    "correlation_id": correlation_id
                }
            )

        return {
            "data": status,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get job status: {str(e)}",
            extra={'correlation_id': correlation_id, 'job_id': job_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve job status",
                "correlation_id": correlation_id
            }
        )


@router.get("/jobs")
async def list_processing_jobs(request: Request) -> Dict[str, Any]:
    """
    List all processing jobs with their current status
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))

    try:
        processor = PDFProcessor()
        jobs = await processor.list_all_jobs()

        return {
            "data": {
                "jobs": jobs,
                "total_count": len(jobs)
            },
            "error": None
        }

    except Exception as e:
        logger.error(
            f"Failed to list jobs: {str(e)}",
            extra={'correlation_id': correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve job list",
                "correlation_id": correlation_id
            }
        )


@router.delete("/jobs/{job_id}")
async def delete_processing_job(
    job_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Delete a processing job and its associated data
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))

    try:
        processor = PDFProcessor()
        success = await processor.delete_job(job_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Job not found",
                    "correlation_id": correlation_id
                }
            )

        return {
            "data": {
                "message": "Job deleted successfully",
                "job_id": job_id
            },
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete job: {str(e)}",
            extra={'correlation_id': correlation_id, 'job_id': job_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to delete job",
                "correlation_id": correlation_id
            }
        )