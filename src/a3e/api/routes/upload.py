"""
File upload and evidence management routes
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import secrets
from datetime import datetime
import logging
from pathlib import Path

from ...core.config import settings
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

@router.post("/evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    accreditor: Optional[str] = Form(None),
    standard_ids: Optional[str] = Form(None),  # Comma-separated
    current_user: dict = Depends(get_current_user)
):
    """Upload evidence document for analysis"""
    try:
        # Validate file
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size (100MB limit)
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        # Generate safe filename and save
        safe_filename = generate_safe_filename(file.filename)
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create evidence record
        evidence_id = f"ev_{secrets.token_hex(8)}"
        
        # In production, this would:
        # 1. Store metadata in database
        # 2. Extract text from document
        # 3. Run through vector embedding
        # 4. Match against standards
        # 5. Queue for analysis
        
        evidence_record = {
            "id": evidence_id,
            "user_id": current_user.get("user_id"),
            "filename": file.filename,
            "safe_filename": safe_filename,
            "file_size": file_size,
            "file_type": file.content_type,
            "title": title or file.filename,
            "description": description,
            "accreditor": accreditor,
            "standard_ids": standard_ids.split(",") if standard_ids else [],
            "status": "processing",
            "uploaded_at": datetime.utcnow().isoformat(),
            "analysis_progress": 0
        }
        
        # Simulate processing start
        logger.info(f"Evidence uploaded: {evidence_id} - {file.filename}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Evidence uploaded successfully. Analysis in progress.",
                "data": evidence_record
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@router.post("/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    accreditor: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple evidence documents"""
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 files per batch upload"
            )
        
        results = []
        
        for file in files:
            # Validate each file
            if not allowed_file(file.filename):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File type not allowed"
                })
                continue
            
            # Process file (simplified for demo)
            try:
                contents = await file.read()
                file_size = len(contents)
                
                if file_size > settings.max_file_size_mb * 1024 * 1024:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "File too large"
                    })
                    continue
                
                # Save file
                safe_filename = generate_safe_filename(file.filename)
                file_path = UPLOAD_DIR / safe_filename
                
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                # Create record
                evidence_id = f"ev_{secrets.token_hex(8)}"
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "evidence_id": evidence_id,
                    "status": "processing"
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r["success"])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Uploaded {successful} of {len(files)} files",
                "data": {
                    "results": results,
                    "total": len(files),
                    "successful": successful,
                    "failed": len(files) - successful
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        raise HTTPException(status_code=500, detail="Batch upload failed")

@router.get("/status/{evidence_id}")
async def get_upload_status(
    evidence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of uploaded evidence"""
    try:
        # In production, fetch from database
        # For demo, return mock status
        
        # Simulate different statuses
        if evidence_id.endswith("_done"):
            status = "completed"
            progress = 100
        elif evidence_id.endswith("_err"):
            status = "failed"
            progress = 0
        else:
            status = "processing"
            progress = 65
        
        return {
            "success": True,
            "data": {
                "evidence_id": evidence_id,
                "status": status,
                "progress": progress,
                "message": f"Analysis {progress}% complete" if status == "processing" else None,
                "results": {
                    "standards_matched": 12,
                    "confidence_score": 0.87,
                    "gaps_identified": 3
                } if status == "completed" else None
            }
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")

@router.get("/list")
async def list_uploads(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List user's uploaded evidence"""
    try:
        # Mock data for demo
        uploads = [
            {
                "id": f"ev_{secrets.token_hex(8)}",
                "filename": "Curriculum_Assessment_Plan_2025.pdf",
                "title": "Curriculum Assessment Plan",
                "uploaded_at": "2025-08-20T10:30:00Z",
                "status": "completed",
                "size": 2457600,
                "standards_matched": 15,
                "confidence_score": 0.92
            },
            {
                "id": f"ev_{secrets.token_hex(8)}",
                "filename": "Student_Learning_Outcomes.docx",
                "title": "Student Learning Outcomes Report",
                "uploaded_at": "2025-08-19T14:15:00Z",
                "status": "completed",
                "size": 1024000,
                "standards_matched": 8,
                "confidence_score": 0.88
            },
            {
                "id": f"ev_{secrets.token_hex(8)}",
                "filename": "Faculty_Qualifications_2025.xlsx",
                "title": "Faculty Qualifications Matrix",
                "uploaded_at": "2025-08-18T09:45:00Z",
                "status": "processing",
                "size": 512000,
                "progress": 75
            }
        ]
        
        # Filter by status if provided
        if status:
            uploads = [u for u in uploads if u["status"] == status]
        
        # Apply pagination
        total = len(uploads)
        uploads = uploads[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "uploads": uploads,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"List uploads error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list uploads")

@router.delete("/{evidence_id}")
async def delete_upload(
    evidence_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete uploaded evidence"""
    try:
        # In production:
        # 1. Verify ownership
        # 2. Delete from storage
        # 3. Remove from database
        # 4. Clean up any analysis results
        
        logger.info(f"Deleting evidence: {evidence_id} for user: {current_user['user_id']}")
        
        return {
            "success": True,
            "message": "Evidence deleted successfully",
            "data": {
                "evidence_id": evidence_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")
