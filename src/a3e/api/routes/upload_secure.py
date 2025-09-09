"""
Secure file upload API with cloud storage support
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import io

from ...services.storage_service import get_storage_service, StorageService
from ...core.auth import get_current_user
from ...models import User, Document
from ...services.database_service import DatabaseService
from ...core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv"
]

class PresignRequest(BaseModel):
    """Request for presigned upload URL"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)
    size: int = Field(..., gt=0, le=MAX_FILE_SIZE)

class PresignResponse(BaseModel):
    """Response with presigned upload URL"""
    upload_url: str
    upload_fields: Dict[str, Any]
    file_key: str
    expires_in: int

class CompleteUploadRequest(BaseModel):
    """Request to complete upload and save metadata"""
    file_key: str
    filename: str
    size: int
    content_type: str
    hash: Optional[str] = None

class UploadResponse(BaseModel):
    """Response for upload operations"""
    success: bool
    message: str
    file_id: Optional[str] = None
    file_key: Optional[str] = None
    download_url: Optional[str] = None

async def get_db():
    """Get database session"""
    settings = get_settings()
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

@router.post("/presign", response_model=PresignResponse)
async def get_presigned_upload_url(
    request: PresignRequest,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Get a presigned URL for direct file upload to storage
    """
    # Validate content type
    if request.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: PDF, Word, Excel, PowerPoint, Text, CSV"
        )
    
    # Validate file size
    if request.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Get presigned URL
    try:
        presign_data = await storage.get_presigned_upload_url(
            org_id=current_user.institution_name or "default",
            user_id=str(current_user.id),
            filename=request.filename,
            content_type=request.content_type,
            max_size=request.size
        )
        
        return PresignResponse(
            upload_url=presign_data["url"],
            upload_fields=presign_data.get("fields", {}),
            file_key=presign_data["key"],
            expires_in=presign_data["expires_in"]
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )

@router.post("/complete", response_model=UploadResponse)
async def complete_upload(
    request: CompleteUploadRequest,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete the upload process by saving metadata to database
    """
    try:
        # Verify the file exists in storage (optional)
        # For S3, we trust that the upload succeeded
        # For local, we can verify the file exists
        
        # Save document metadata to database
        document = Document(
            user_id=current_user.id,
            filename=request.filename,
            storage_key=request.file_key,
            content_type=request.content_type,
            size=request.size,
            hash=request.hash,
            uploaded_at=datetime.utcnow(),
            status="uploaded"
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Generate download URL
        download_url = await storage.get_download_url(
            file_key=request.file_key,
            filename=request.filename
        )
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=str(document.id),
            file_key=request.file_key,
            download_url=download_url
        )
    except Exception as e:
        logger.error(f"Failed to complete upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save upload metadata"
        )

@router.post("/direct", response_model=UploadResponse)
async def upload_file_direct(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Direct file upload endpoint (fallback for when presigned URLs aren't available)
    """
    # Validate content type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: PDF, Word, Excel, PowerPoint, Text, CSV"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        # Generate file key
        file_key = storage.generate_file_key(
            org_id=current_user.institution_name or "default",
            user_id=str(current_user.id),
            filename=file.filename
        )
        
        # Save file to storage
        save_result = await storage.save_file(
            file_content=content,
            file_key=file_key,
            content_type=file.content_type,
            metadata={
                "original_name": file.filename,
                "user_id": str(current_user.id),
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
        
        # Save document metadata to database
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            storage_key=file_key,
            content_type=file.content_type,
            size=save_result["size"],
            hash=save_result["hash"],
            uploaded_at=datetime.utcnow(),
            status="uploaded"
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Generate download URL
        download_url = await storage.get_download_url(
            file_key=file_key,
            filename=file.filename
        )
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=str(document.id),
            file_key=file_key,
            download_url=download_url
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/files")
async def list_user_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """
    List files uploaded by the current user
    """
    try:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == current_user.id)
            .order_by(Document.uploaded_at.desc())
            .limit(limit)
        )
        documents = result.scalars().all()
        
        return {
            "files": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "size": doc.size,
                    "content_type": doc.content_type,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "status": doc.status
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files"
        )

@router.get("/download/{file_key}")
async def download_file(
    file_key: str,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a file (for local storage)
    """
    try:
        # Verify user owns the file
        result = await db.execute(
            select(Document)
            .where(Document.storage_key == file_key)
            .where(Document.user_id == current_user.id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get file content
        content = await storage.get_file(file_key)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not found"
            )
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=document.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file
    """
    try:
        # Get document
        result = await db.execute(
            select(Document)
            .where(Document.id == file_id)
            .where(Document.user_id == current_user.id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete from storage
        await storage.delete_file(document.storage_key)
        
        # Delete from database
        await db.delete(document)
        await db.commit()
        
        return {"success": True, "message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )