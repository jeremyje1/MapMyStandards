"""
Enhanced upload routes with job tracking and real progress
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
import json
import secrets
import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ...core.config import settings
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Job status storage (in production use Redis/DB)
JOBS_DIR = Path("jobs_status")
JOBS_DIR.mkdir(exist_ok=True)

# In-memory storage for demo (use database in production)
upload_store: Dict[str, Dict[str, Any]] = {}

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'md', 
    'png', 'jpg', 'jpeg', 'gif', 'pptx', 'ppt'
}

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_safe_filename(original_filename: str) -> str:
    """Generate a safe filename with unique ID"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}.{ext}"
    return safe_name

def save_job_status(job_id: str, status_data: Dict[str, Any]):
    """Save job status to persistent storage"""
    try:
        job_file = JOBS_DIR / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(status_data, f, indent=2, default=str)
        
        # Also keep in memory for fast access
        upload_store[job_id] = status_data
    except Exception as e:
        logger.error(f"Failed to save job status {job_id}: {e}")

def load_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Load job status from storage"""
    try:
        # Try memory first
        if job_id in upload_store:
            return upload_store[job_id]
        
        # Try file system
        job_file = JOBS_DIR / f"{job_id}.json"
        if job_file.exists():
            with open(job_file, 'r') as f:
                status_data = json.load(f)
                upload_store[job_id] = status_data  # Cache in memory
                return status_data
        return None
    except Exception as e:
        logger.error(f"Failed to load job status {job_id}: {e}")
        return None

async def simulate_document_analysis(job_id: str, file_path: Path, original_filename: str):
    """
    Simulate document analysis with realistic progress steps
    In production this would:
    1. Extract text from PDF/DOCX
    2. Chunk content 
    3. Generate embeddings
    4. Match against standards database
    5. Calculate gaps and coverage
    """
    try:
        steps = [
            ("extracting", "Extracting text from document", 10),
            ("parsing", "Parsing document structure", 25),
            ("embedding", "Generating content embeddings", 50),
            ("matching", "Matching against SACSCOC standards", 75),
            ("analyzing", "Computing gaps and coverage", 90),
            ("completed", "Analysis complete", 100)
        ]
        
        for step, description, progress in steps:
            # Update status
            status_data = load_job_status(job_id) or {}
            status_data.update({
                "status": step,
                "progress": progress,
                "description": description,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            if step == "completed":
                # Add mock analysis results
                status_data.update({
                    "results": {
                        "standards_matched": 8,
                        "total_standards": 12,
                        "confidence_score": 0.87,
                        "gaps_identified": 4,
                        "coverage_percentage": 67,
                        "mapped_standards": [
                            {"standard_id": "SACSCOC_1_1", "title": "Mission", "confidence": 0.92, "excerpts": ["Our mission is to...", "We are committed to..."]},
                            {"standard_id": "SACSCOC_2_1", "title": "Degree Standards", "confidence": 0.85, "excerpts": ["Bachelor degree requires 120 credit hours..."]},
                            {"standard_id": "SACSCOC_8_1", "title": "Faculty", "confidence": 0.78, "excerpts": ["Faculty qualifications include..."]}
                        ],
                        "gaps": [
                            {"standard_id": "SACSCOC_9_1", "title": "Academic Support Services", "severity": "medium", "description": "Limited evidence of tutoring programs"},
                            {"standard_id": "SACSCOC_10_1", "title": "Financial Resources", "severity": "high", "description": "Missing audited financial statements"}
                        ]
                    }
                })
            
            save_job_status(job_id, status_data)
            
            # Realistic delay between steps
            await asyncio.sleep(2 if step != "completed" else 1)
            
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        status_data = load_job_status(job_id) or {}
        status_data.update({
            "status": "failed",
            "progress": 0,
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })
        save_job_status(job_id, status_data)

@router.post("", status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    accreditor: Optional[str] = Form("sacscoc"),
    current_user: dict = Depends(get_current_user)
):
    """Upload file and start analysis automatically"""
    try:
        # Validate file
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > (settings.max_file_size_mb * 1024 * 1024):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        # Generate IDs and save file
        job_id = f"job_{secrets.token_hex(12)}"
        file_id = f"file_{secrets.token_hex(8)}"
        safe_filename = generate_safe_filename(file.filename)
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create initial job record
        job_data = {
            "job_id": job_id,
            "file_id": file_id,
            "user_id": current_user.get("user_id"),
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_size": file_size,
            "file_type": file.content_type,
            "title": title or file.filename,
            "description": description or "",
            "accreditor": accreditor or "sacscoc",
            "status": "queued",
            "progress": 0,
            "description": "Upload complete, analysis queued",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        save_job_status(job_id, job_data)
        
        # Start background analysis
        background_tasks.add_task(
            simulate_document_analysis, 
            job_id, 
            file_path, 
            file.filename
        )
        
        logger.info(f"File uploaded and analysis started: {job_id} - {file.filename}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "File uploaded successfully. Analysis started.",
                "data": {
                    "job_id": job_id,
                    "file_id": file_id,
                    "filename": file.filename,
                    "status": "queued",
                    "progress": 0,
                    "estimated_completion_minutes": 3
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@router.get("/{file_id}")
async def get_file_status(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get file processing status and results"""
    try:
        # Find job by file_id
        job_data = None
        for job_id, data in upload_store.items():
            if data.get("file_id") == file_id:
                job_data = data
                break
        
        if not job_data:
            # Check filesystem
            for job_file in JOBS_DIR.glob("*.json"):
                data = load_job_status(job_file.stem)
                if data and data.get("file_id") == file_id:
                    job_data = data
                    break
        
        if not job_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check ownership
        if job_data.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "data": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get job processing status by job ID"""
    try:
        job_data = load_job_status(job_id)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check ownership
        if job_data.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "data": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job status error: {e}")
        raise HTTPException(status_code=500, detail="Job status check failed")

@router.post("/analysis/start")
async def start_analysis(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger analysis of uploaded files"""
    try:
        # Get user's files that aren't analyzed yet
        user_files = []
        for job_id, data in upload_store.items():
            if (data.get("user_id") == current_user.get("user_id") and 
                data.get("status") in ["queued", "failed"]):
                user_files.append((job_id, data))
        
        if not user_files:
            return {
                "success": True,
                "message": "No files available for analysis",
                "data": {"files_processed": 0}
            }
        
        # Start analysis for each file
        for job_id, data in user_files:
            file_path = UPLOAD_DIR / data["safe_filename"]
            if file_path.exists():
                background_tasks.add_task(
                    simulate_document_analysis,
                    job_id,
                    file_path,
                    data["filename"]
                )
        
        return {
            "success": True,
            "message": f"Analysis started for {len(user_files)} files",
            "data": {
                "files_processed": len(user_files),
                "estimated_completion_minutes": len(user_files) * 3
            }
        }
        
    except Exception as e:
        logger.error(f"Start analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")

@router.get("")
async def list_user_files(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List user's uploaded files"""
    try:
        # Get all user files
        user_files = []
        for job_id, data in upload_store.items():
            if data.get("user_id") == current_user.get("user_id"):
                user_files.append(data)
        
        # Load from filesystem if memory is empty
        if not user_files:
            for job_file in JOBS_DIR.glob("*.json"):
                data = load_job_status(job_file.stem)
                if data and data.get("user_id") == current_user.get("user_id"):
                    user_files.append(data)
        
        # Filter by status
        if status:
            user_files = [f for f in user_files if f.get("status") == status]
        
        # Sort by creation date (newest first)
        user_files.sort(
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
        # Apply pagination
        total = len(user_files)
        user_files = user_files[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "files": user_files,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete uploaded file and analysis results"""
    try:
        # Find and remove job
        job_to_delete = None
        for job_id, data in list(upload_store.items()):
            if (data.get("file_id") == file_id and 
                data.get("user_id") == current_user.get("user_id")):
                job_to_delete = (job_id, data)
                break
        
        if not job_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        job_id, job_data = job_to_delete
        
        # Delete file from filesystem
        try:
            file_path = UPLOAD_DIR / job_data["safe_filename"]
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {e}")
        
        # Delete job status
        try:
            job_file = JOBS_DIR / f"{job_id}.json"
            if job_file.exists():
                job_file.unlink()
        except Exception as e:
            logger.warning(f"Could not delete job file {job_file}: {e}")
        
        # Remove from memory
        upload_store.pop(job_id, None)
        
        logger.info(f"Deleted file: {file_id} for user: {current_user['user_id']}")
        
        return {
            "success": True,
            "message": "File deleted successfully",
            "data": {
                "file_id": file_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")