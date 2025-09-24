"""
PDF processing pipeline using PyPDF2 for text extraction and chunking
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import uuid

import PyPDF2
from sentence_transformers import SentenceTransformer

from ..config.settings import get_settings
from .text_cleaner import TextCleaner
from .content_manager import ContentManager
from .quality_validator import QualityValidator

logger = logging.getLogger(__name__)


class ProcessingJob:
    """Processing job status tracking"""

    def __init__(self, job_id: str, filename: str):
        self.job_id = job_id
        self.filename = filename
        self.status = "queued"  # queued, processing, completed, failed
        self.progress_percent = 0.0
        self.message = "Job queued for processing"
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at = None
        self.error_details = None


class PDFProcessor:
    """
    Main PDF processing pipeline with text extraction, chunking, and embedding generation
    """

    def __init__(self):
        self.settings = get_settings()
        self.text_cleaner = TextCleaner()
        self.content_manager = ContentManager()
        self.quality_validator = QualityValidator()
        self.embedding_model = None
        self.jobs: Dict[str, ProcessingJob] = {}

    async def _load_embedding_model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self.embedding_model is None:
            logger.info(f"Loading embedding model: {self.settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(self.settings.EMBEDDING_MODEL)
        return self.embedding_model

    def _extract_pdf_text(self, file_path: str, correlation_id: str) -> List[Tuple[str, int]]:
        """
        Extract text from PDF with page references

        Returns:
            List of (text_content, page_number) tuples
        """
        try:
            pages_text = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                logger.info(
                    f"Processing PDF with {total_pages} pages",
                    extra={'correlation_id': correlation_id}
                )

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            # Basic text validation
                            if len(text.strip()) >= self.settings.MIN_TEXT_LENGTH:
                                pages_text.append((text, page_num))
                        else:
                            logger.warning(
                                f"No text extracted from page {page_num}",
                                extra={'correlation_id': correlation_id}
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract text from page {page_num}: {str(e)}",
                            extra={'correlation_id': correlation_id}
                        )
                        continue

                if not pages_text:
                    raise ValueError("No readable text found in PDF")

                logger.info(
                    f"Successfully extracted text from {len(pages_text)}/{total_pages} pages",
                    extra={'correlation_id': correlation_id}
                )

                return pages_text

        except Exception as e:
            logger.error(
                f"PDF text extraction failed: {str(e)}",
                extra={'correlation_id': correlation_id}
            )
            raise

    def _chunk_text(self, text: str, page_number: int) -> List[Dict[str, Any]]:
        """
        Chunk text into paragraph-level segments

        Args:
            text: Raw text from PDF page
            page_number: Source page number

        Returns:
            List of text chunks with metadata
        """
        # Clean the text first
        cleaned_text = self.text_cleaner.clean_text(text)

        if not cleaned_text or len(cleaned_text) < self.settings.MIN_TEXT_LENGTH:
            return []

        chunks = []

        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', cleaned_text)

        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding this paragraph would exceed max chunk size, save current chunk
            if current_size + len(paragraph) > self.settings.MAX_CHUNK_SIZE and current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'page_number': page_number,
                    'chunk_size': current_size
                })

                # Start new chunk with overlap if configured
                if self.settings.CHUNK_OVERLAP > 0:
                    overlap_text = current_chunk[-self.settings.CHUNK_OVERLAP:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                    current_size = len(current_chunk)
                else:
                    current_chunk = paragraph
                    current_size = len(paragraph)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size = len(current_chunk)

        # Add remaining chunk
        if current_chunk and current_size >= self.settings.MIN_TEXT_LENGTH:
            chunks.append({
                'content': current_chunk.strip(),
                'page_number': page_number,
                'chunk_size': current_size
            })

        return chunks

    def _extract_metadata(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Extract metadata from filename and content

        Args:
            filename: Original PDF filename
            content: Text content for analysis

        Returns:
            Extracted metadata dictionary
        """
        metadata = {
            'manufacturer': 'Unknown',
            'model_series': 'Unknown',
            'content_type': 'troubleshooting',
            'source_manual': filename
        }

        filename_lower = filename.lower()
        content_lower = content.lower()

        # Extract manufacturer from filename or content
        manufacturers = ['whirlpool', 'lg', 'samsung', 'ge', 'kenmore', 'maytag', 'bosch']

        for manufacturer in manufacturers:
            if manufacturer in filename_lower or manufacturer in content_lower:
                metadata['manufacturer'] = manufacturer.title()
                break

        # Determine content type based on keywords
        if any(keyword in content_lower for keyword in ['troubleshoot', 'problem', 'error', 'issue']):
            metadata['content_type'] = 'troubleshooting'
        elif any(keyword in content_lower for keyword in ['maintenance', 'clean', 'service']):
            metadata['content_type'] = 'maintenance'
        elif any(keyword in content_lower for keyword in ['safety', 'warning', 'caution']):
            metadata['content_type'] = 'safety'
        elif any(keyword in content_lower for keyword in ['warranty', 'guarantee']):
            metadata['content_type'] = 'warranty'

        # Extract model information (basic pattern matching)
        model_patterns = [
            r'\b([A-Z]{2,}\d{3,})\b',  # Common model patterns like WTW5000
            r'\bmodel\s+([A-Z0-9\-]+)\b'
        ]

        for pattern in model_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                metadata['model_series'] = matches[0]
                break

        return metadata

    async def process_pdf_file(self, file_path: str, job_id: str, correlation_id: str) -> bool:
        """
        Main processing pipeline for PDF files

        Args:
            file_path: Path to uploaded PDF file
            job_id: Unique job identifier
            correlation_id: Request correlation ID

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            job = ProcessingJob(job_id, Path(file_path).name)
            self.jobs[job_id] = job

        try:
            job.status = "processing"
            job.message = "Extracting text from PDF"
            job.progress_percent = 10.0

            logger.info(
                f"Starting PDF processing: {file_path}",
                extra={'correlation_id': correlation_id, 'job_id': job_id}
            )

            # Extract text from PDF
            pages_text = self._extract_pdf_text(file_path, correlation_id)
            job.progress_percent = 30.0
            job.message = "Cleaning and chunking text"

            # Process each page and create chunks
            all_chunks = []
            for page_text, page_num in pages_text:
                chunks = self._chunk_text(page_text, page_num)
                all_chunks.extend(chunks)

            if not all_chunks:
                raise ValueError("No valid text chunks extracted from PDF")

            job.progress_percent = 50.0
            job.message = f"Processing {len(all_chunks)} text chunks"

            # Load embedding model
            embedding_model = await self._load_embedding_model()
            job.progress_percent = 60.0
            job.message = "Generating embeddings"

            # Process chunks in batches
            batch_size = self.settings.EMBEDDING_BATCH_SIZE
            processed_count = 0

            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]

                # Generate embeddings for batch
                texts = [chunk['content'] for chunk in batch_chunks]
                embeddings = embedding_model.encode(texts)

                # Store content and embeddings
                for chunk, embedding in zip(batch_chunks, embeddings):
                    # Extract metadata
                    metadata = self._extract_metadata(job.filename, chunk['content'])

                    # Validate quality
                    quality_score = await self.quality_validator.calculate_readability_score(
                        chunk['content']
                    )

                    if quality_score < self.settings.MIN_READABILITY_SCORE:
                        logger.warning(
                            f"Chunk quality below threshold: {quality_score}",
                            extra={'correlation_id': correlation_id, 'job_id': job_id}
                        )
                        continue

                    # Store in database and vector store
                    await self.content_manager.store_content_chunk(
                        content=chunk['content'],
                        metadata=metadata,
                        embedding=embedding.tolist(),
                        page_reference=f"page_{chunk['page_number']}",
                        confidence_score=quality_score,
                        correlation_id=correlation_id
                    )

                    processed_count += 1

                # Update progress
                progress = 60.0 + (40.0 * (i + batch_size) / len(all_chunks))
                job.progress_percent = min(progress, 95.0)

            # Final quality check and duplicate detection
            job.message = "Running quality validation"
            await self.quality_validator.check_for_duplicates(correlation_id)

            # Cleanup uploaded file
            try:
                Path(file_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup file: {e}")

            job.status = "completed"
            job.progress_percent = 100.0
            job.message = f"Processing completed - {processed_count} chunks stored"
            job.completed_at = datetime.utcnow().isoformat()

            logger.info(
                f"PDF processing completed: {processed_count} chunks stored",
                extra={'correlation_id': correlation_id, 'job_id': job_id}
            )

            return True

        except Exception as e:
            job.status = "failed"
            job.error_details = str(e)
            job.message = f"Processing failed: {str(e)}"
            job.completed_at = datetime.utcnow().isoformat()

            logger.error(
                f"PDF processing failed: {str(e)}",
                extra={'correlation_id': correlation_id, 'job_id': job_id}
            )

            return False

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get processing job status"""
        job = self.jobs.get(job_id)
        if not job:
            return None

        return {
            'job_id': job.job_id,
            'status': job.status,
            'filename': job.filename,
            'progress_percent': job.progress_percent,
            'message': job.message,
            'created_at': job.created_at,
            'completed_at': job.completed_at,
            'error_details': job.error_details
        }

    async def list_all_jobs(self) -> List[Dict[str, Any]]:
        """List all processing jobs"""
        return [await self.get_job_status(job_id) for job_id in self.jobs.keys()]

    async def delete_job(self, job_id: str) -> bool:
        """Delete a processing job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False