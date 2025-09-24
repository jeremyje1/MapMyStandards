"""
Enhanced documents API with S3 integration
Simplified version without notification complexity
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import jwt
from jwt.exceptions import InvalidTokenError

from ...database.connection import db_manager
from ...models.user import User
from ...models.document import Document
from ...services.storage_service import StorageService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
security = HTTPBearer()

# Initialize settings and storage service
settings = get_settings()
storage_service = StorageService(settings)

JWT_ALGORITHM = "HS256"

# Database dependency
async def get_db():
    """Get database session."""
    async with db_manager.get_session() as session:
        yield session

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_manager.get_session() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
            
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'md',
    'png', 'jpg', 'jpeg', 'gif', 'pptx', 'ppt'
}

def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def validate_file(file: UploadFile) -> bool:
    """Validate file type and size."""
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{ext} not allowed"
        )
    
    # Check file size (10MB max)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )
    
    return True

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: Optional[str] = Form("general"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document with S3 integration."""
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique file key
        file_id = str(uuid.uuid4())
        file_extension = get_file_extension(file.filename)
        s3_key = f"documents/{current_user.id}/{file_id}.{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to S3
        try:
            s3_url = storage_service.upload_file(
                file_key=s3_key,
                file_content=file_content,
                content_type=file.content_type or 'application/octet-stream'
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Create database record
        document = Document(
            id=file_id,
            user_id=current_user.id,
            filename=file.filename,
            file_key=s3_key,
            file_size=file.size or len(file_content),
            content_type=file.content_type,
            status="uploaded",
            category=category,
            upload_date=datetime.utcnow()
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Return success response
        return {
            "status": "success",
            "document_id": document.id,
            "filename": document.filename,
            "size": document.file_size,
            "category": category,
            "upload_date": document.upload_date.isoformat(),
            "s3_key": s3_key,
            "url": s3_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for the current user."""
    return await _list_documents_impl(skip, limit, category, db, current_user)

@router.get("/list", status_code=status.HTTP_200_OK)
async def list_documents_alt(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for the current user (alternative endpoint)."""
    return await _list_documents_impl(skip, limit, category, db, current_user)

async def _list_documents_impl(
    skip: int,
    limit: int,
    category: Optional[str],
    db: Session,
    current_user: User
):
    try:
        query = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.status != "deleted"
        )
        
        if category:
            query = query.filter(Document.category == category)
        
        total = query.count()
        documents = query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "original_name": doc.filename,
                    "size": doc.file_size,
                    "content_type": doc.content_type,
                    "category": doc.category,
                    "status": doc.status,
                    "uploaded_at": doc.upload_date.isoformat() if doc.upload_date else None,
                    "created_at": doc.upload_date.isoformat() if doc.upload_date else None
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )

@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
        Document.status != "deleted"
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "status": "success",
        "document": {
            "id": document.id,
            "filename": document.filename,
            "size": document.file_size,
            "content_type": document.content_type,
            "category": document.category,
            "status": document.status,
            "upload_date": document.upload_date.isoformat() if document.upload_date else None
        }
    }

@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get download URL for a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
        Document.status != "deleted"
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Get presigned download URL from S3
        download_url = storage_service.get_presigned_download_url(
            file_key=document.file_key,
            filename=document.filename
        )
        
        return {
            "status": "success",
            "download_url": download_url,
            "filename": document.filename,
            "expires_in": 3600  # 1 hour
        }
    except Exception as e:
        logger.error(f"Download URL generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
        Document.status != "deleted"
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete from S3
        try:
            storage_service.delete_file(document.file_key)
        except Exception as e:
            logger.warning(f"S3 deletion failed: {str(e)}")
        
        # Mark as deleted in database
        document.status = "deleted"
        db.commit()
        
        return {
            "status": "success",
            "message": "Document deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

@router.get("/notifications", status_code=status.HTTP_200_OK)
async def get_notifications(
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user (simplified version)."""
    # For now, just return empty notifications
    # In production, implement with Redis or database
    return {
        "status": "success",
        "notifications": []
    }
