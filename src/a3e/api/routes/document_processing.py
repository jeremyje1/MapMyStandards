"""
Real Document Processing API with AI Integration

This module provides the actual document processing pipeline that:
1. Accepts document uploads
2. Extracts text content
3. Uses AI to map evidence to standards
4. Calculates compliance metrics
5. Returns real, actionable data (not demo data)
"""

import asyncio
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ...services.evidence_processor import EvidenceProcessor
from ...services.ai_service import get_ai_service
from ...services.database_service import DatabaseService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/processing", tags=["document-processing"])

settings = get_settings()


class ProcessingResponse(BaseModel):
    """Response model for document processing"""
    document_id: str
    filename: str
    status: str
    processing_time: float
    extracted_text_preview: Optional[str]
    identified_standards: List[Dict[str, Any]]
    compliance_score: float
    gaps_identified: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class ProcessingStatus(BaseModel):
    """Status of document processing"""
    document_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    current_step: str
    estimated_time_remaining: Optional[int]
    results_available: bool


# In-memory storage for processing status (should be replaced with Redis in production)
processing_jobs = {}


async def get_db_service():
    """Database service dependency"""
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()


async def process_document_async(
    document_id: str,
    file_content: bytes,
    filename: str,
    metadata: Dict[str, Any]
):
    """
    Asynchronous document processing with real AI analysis
    """
    try:
        # Update status
        processing_jobs[document_id] = {
            "status": "processing",
            "progress": 10,
            "current_step": "Extracting text from document"
        }
        
        # Initialize processor
        processor = EvidenceProcessor(settings)
        
        # Save file temporarily
        temp_path = Path(f"/tmp/{document_id}_{filename}")
        temp_path.write_bytes(file_content)
        
        # Process document
        processing_jobs[document_id]["progress"] = 30
        processing_jobs[document_id]["current_step"] = "Analyzing document content with AI"
        
        result = await processor.process_document(temp_path, metadata)
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        # Update final status
        processing_jobs[document_id] = {
            "status": "completed",
            "progress": 100,
            "current_step": "Processing complete",
            "results": result
        }
        
        logger.info(f"✅ Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing document {document_id}: {e}")
        processing_jobs[document_id] = {
            "status": "failed",
            "progress": 0,
            "current_step": "Processing failed",
            "error": str(e)
        }


@router.post("/upload", response_model=ProcessingResponse)
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    institution_id: str = Form(...),
    accreditor: str = Form("SACSCOC"),
    document_type: str = Form("evidence"),
    auto_process: bool = Form(True)
):
    """
    Upload and process a document with real AI analysis
    
    This endpoint:
    1. Accepts document uploads
    2. Validates file type and size
    3. Initiates AI-powered processing
    4. Returns real metrics and mappings
    """
    try:
        # Validate file type
        allowed_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (100MB limit)
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 100MB limit"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = {
            "id": document_id,
            "filename": file.filename,
            "institution_id": institution_id,
            "accreditor": accreditor,
            "document_type": document_type,
            "file_size": file_size,
            "content_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        # Initialize processing status
        processing_jobs[document_id] = {
            "status": "pending",
            "progress": 0,
            "current_step": "Upload received, queued for processing"
        }
        
        if auto_process:
            # Start background processing
            background_tasks.add_task(
                process_document_async,
                document_id,
                file_content,
                file.filename,
                metadata
            )
            
            # Return immediate response
            return ProcessingResponse(
                document_id=document_id,
                filename=file.filename,
                status="processing",
                processing_time=0.0,
                extracted_text_preview="Processing started...",
                identified_standards=[],
                compliance_score=0.0,
                gaps_identified=[],
                recommendations=["Document is being processed. Check status for updates."],
                metadata=metadata
            )
        else:
            # Return without processing
            return ProcessingResponse(
                document_id=document_id,
                filename=file.filename,
                status="uploaded",
                processing_time=0.0,
                extracted_text_preview="Document uploaded successfully",
                identified_standards=[],
                compliance_score=0.0,
                gaps_identified=[],
                recommendations=["Use the process endpoint to analyze this document"],
                metadata=metadata
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{document_id}", response_model=ProcessingStatus)
async def get_processing_status(document_id: str):
    """
    Get the current processing status of a document
    """
    if document_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    job = processing_jobs[document_id]
    
    return ProcessingStatus(
        document_id=document_id,
        status=job["status"],
        progress=job.get("progress", 0),
        current_step=job.get("current_step", "Unknown"),
        estimated_time_remaining=None,  # Could calculate based on progress
        results_available=job["status"] == "completed"
    )


@router.get("/results/{document_id}", response_model=ProcessingResponse)
async def get_processing_results(document_id: str):
    """
    Get the processing results for a completed document
    """
    if document_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    job = processing_jobs[document_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Document processing not complete. Status: {job['status']}"
        )
    
    results = job.get("results", {})
    
    return ProcessingResponse(
        document_id=document_id,
        filename=results.get("filename", "Unknown"),
        status="completed",
        processing_time=results.get("processing_time", 0.0),
        extracted_text_preview=results.get("text_preview", ""),
        identified_standards=results.get("standard_mappings", []),
        compliance_score=results.get("compliance_score", 0.0),
        gaps_identified=results.get("gaps", []),
        recommendations=results.get("recommendations", []),
        metadata=results.get("metadata", {})
    )


@router.get("/recent")
async def get_recent_uploads(
    limit: int = 10,
    institution_id: Optional[str] = None
):
    """
    Get recent document uploads (real data, not demo)
    """
    recent = []
    
    for doc_id, job in list(processing_jobs.items())[:limit]:
        if institution_id and job.get("metadata", {}).get("institution_id") != institution_id:
            continue
            
        recent.append({
            "document_id": doc_id,
            "filename": job.get("results", {}).get("filename", "Processing..."),
            "status": job["status"],
            "uploaded_at": job.get("metadata", {}).get("uploaded_at", ""),
            "compliance_score": job.get("results", {}).get("compliance_score", 0.0)
        })
    
    return {"recent_uploads": recent}


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its processing results
    """
    if document_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    
    del processing_jobs[document_id]
    
    return {"message": f"Document {document_id} deleted successfully"}