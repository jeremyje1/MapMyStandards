"""
File upload API with local storage fallback (no AWS required)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import hashlib
import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
import logging

from ...models.user import User
from ...models.document import Document
from ...core.database import get_db
from .auth_enhanced import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Configuration for local storage
UPLOAD_DIR = Path("/app/uploads") if os.path.exists("/app") else Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/msword",
    "text/plain",
    "text/csv",
]

# Pydantic models
class SimpleUploadResponse(BaseModel):
    id: str
    filename: str
    file_key: str
    file_size: int
    status: str
    uploaded_at: str
    download_url: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_key: str
    file_size: int
    content_type: str
    status: str
    uploaded_at: str
    download_url: str

@router.post("/simple", response_model=SimpleUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simple file upload to local storage (no AWS required)
    """
    try:
        # Validate file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Validate content type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )
        
        # Generate unique file key
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_key = f"{current_user.get('id')}/{file_uuid}{file_extension}"
        
        # Create user directory
        user_dir = UPLOAD_DIR / str(current_user.get("id"))
        user_dir.mkdir(exist_ok=True, parents=True)
        
        # Save file to local storage
        file_path = UPLOAD_DIR / file_key
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Calculate file hash
        sha256 = hashlib.sha256(contents).hexdigest()
        
        # Create document record
        document = Document(
            user_id=current_user.get("id"),
            organization_id=current_user.institution_name,
            filename=file.filename,
            file_key=file_key,
            file_size=file_size,
            content_type=file.content_type,
            sha256=sha256,
            status="uploaded",
            uploaded_at=datetime.utcnow()
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Generate download URL
        base_url = os.getenv("API_URL", "https://api.mapmystandards.ai")
        download_url = f"{base_url}/upload/download/{document.id}"
        
        return SimpleUploadResponse(
            id=str(document.id),
            filename=document.filename,
            file_key=document.file_key,
            file_size=document.file_size,
            status=document.status,
            uploaded_at=document.uploaded_at.isoformat(),
            download_url=download_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.get("/download/{document_id}")
async def download_file(
    document_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a file from local storage
    """
    try:
        # Get document record
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.get("id")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if file exists
        file_path = UPLOAD_DIR / document.file_key
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found in storage")
        
        # Return file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=document.filename,
            media_type=document.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    List user's uploaded documents
    """
    try:
        documents = db.query(Document).filter(
            Document.user_id == current_user.get("id"),
            Document.status != "deleted"
        ).order_by(
            Document.uploaded_at.desc()
        ).limit(limit).offset(offset).all()
        
        base_url = os.getenv("API_URL", "https://api.mapmystandards.ai")
        
        result = []
        for doc in documents:
            result.append(DocumentResponse(
                id=str(doc.id),
                filename=doc.filename,
                file_key=doc.file_key,
                file_size=doc.file_size,
                content_type=doc.content_type,
                status=doc.status,
                uploaded_at=doc.uploaded_at.isoformat(),
                download_url=f"{base_url}/upload/download/{doc.id}"
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document (soft delete)
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.get("id")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Mark as deleted (keep file for recovery)
        document.status = "deleted"
        document.deleted_at = datetime.utcnow()
        db.commit()
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")