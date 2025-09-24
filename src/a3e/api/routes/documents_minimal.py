"""
Minimal documents API - uses same pattern as intelligence-simple
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import logging
import jwt
from datetime import datetime
import uuid

from ...core.config import get_settings
from ...services.storage_service import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
security = HTTPBearer()

settings = get_settings()
storage_service = StorageService(settings)

JWT_ALGORITHM = "HS256"

# Simple auth check
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"user_id": user_id}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    """Upload a document."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        storage_key = f"documents/{user['user_id']}/{file_id}.{ext}" if ext else f"documents/{user['user_id']}/{file_id}"
        
        # Read file content
        content = await file.read()
        
        # Upload to S3
        result = await storage_service.upload_file(
            file_content=content,
            file_name=storage_key,
            content_type=file.content_type or 'application/octet-stream'
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to upload file")
        
        # Return simple response
        return {
            "status": "success",
            "document_id": file_id,
            "filename": file.filename,
            "file_size": len(content),
            "upload_date": datetime.utcnow().isoformat(),
            "s3_key": storage_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", status_code=status.HTTP_200_OK)
async def list_documents(
    user: dict = Depends(verify_token)
):
    """List all documents for the current user."""
    try:
        # For now, return empty list since we don't have DB storage
        # In production, this would query the database
        return {
            "status": "success",
            "total": 0,
            "documents": []
        }
    except Exception as e:
        logger.error(f"List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", status_code=status.HTTP_200_OK)
async def list_documents_root(
    user: dict = Depends(verify_token)
):
    """List all documents (root endpoint)."""
    return await list_documents(user)

@router.get("/notifications", status_code=status.HTTP_200_OK)
async def get_notifications(
    user: dict = Depends(verify_token)
):
    """Get notifications (placeholder)."""
    return {
        "status": "success",
        "notifications": []
    }

@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_document(
    document_id: str,
    user: dict = Depends(verify_token)
):
    """Download a document."""
    # Placeholder for now
    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    user: dict = Depends(verify_token)
):
    """Delete a document."""
    # Placeholder for now
    return {
        "status": "success",
        "message": "Document deleted"
    }