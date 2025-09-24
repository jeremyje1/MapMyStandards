"""
Enhanced documents API with S3 integration and real-time notifications
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ...core.database import get_db
from ..dependencies import get_current_user
from ...models.user import User
from ...models.document import Document
from ...services.storage_service import StorageService
from ...core.config import settings
import uuid
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize storage service
storage_service = StorageService(settings)

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'md',
    'png', 'jpg', 'jpeg', 'gif', 'pptx', 'ppt'
}

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# In-memory notification queue (in production, use Redis/RabbitMQ)
notifications = {}

def send_notification(user_id: str, notification: Dict[str, Any]):
    """Send real-time notification to user"""
    if user_id not in notifications:
        notifications[user_id] = []
    notifications[user_id].append({
        **notification,
        "timestamp": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4())
    })
    logger.info(f"Notification sent to user {user_id}: {notification['type']}")

@router.get("/")
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's documents with metadata"""
    try:
        # Get documents from database
        documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).order_by(Document.created_at.desc()).all()
        
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "original_name": doc.original_name,
                    "category": doc.category,
                    "size": doc.size,
                    "content_type": doc.content_type,
                    "uploaded_at": doc.created_at.isoformat(),
                    "status": doc.status,
                    "s3_key": doc.s3_key,
                    "url": doc.url
                }
                for doc in documents
            ],
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("general"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document with S3 storage and real-time progress"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size (10MB limit)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )
    
    # Generate file key
    org_id = current_user.organization or "default"
    file_key = storage_service.generate_file_key(org_id, str(current_user.id), file.filename)
    
    # Send upload started notification
    send_notification(str(current_user.id), {
        "type": "upload_started",
        "filename": file.filename,
        "size": file_size
    })
    
    try:
        # Upload to storage
        if storage_service.storage_type == "s3":
            # Upload to S3
            upload_result = await storage_service.upload_file(
                file_content=file_content,
                file_key=file_key,
                content_type=file.content_type or "application/octet-stream",
                metadata={
                    "original_name": file.filename,
                    "user_id": str(current_user.id),
                    "category": category
                }
            )
            storage_url = upload_result.get("url", "")
        else:
            # Local storage fallback
            local_path = Path("uploads") / file_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(file_content)
            storage_url = f"/uploads/{file_key}"
        
        # Create database record
        document = Document(
            id=uuid.uuid4(),
            user_id=current_user.id,
            filename=file_key.split("/")[-1],
            original_name=file.filename,
            category=category,
            size=file_size,
            content_type=file.content_type,
            s3_key=file_key if storage_service.storage_type == "s3" else None,
            url=storage_url,
            status="processed"
        )
        
        db.add(document)
        db.commit()
        
        # Send upload success notification
        send_notification(str(current_user.id), {
            "type": "upload_success",
            "filename": file.filename,
            "document_id": str(document.id)
        })
        
        # Process document in background (e.g., extract text, generate preview)
        background_tasks.add_task(process_document_async, str(document.id), file_content)
        
        return {
            "message": "Document uploaded successfully",
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "original_name": document.original_name,
                "category": document.category,
                "size": document.size,
                "uploaded_at": document.created_at.isoformat(),
                "status": document.status,
                "url": document.url
            }
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        
        # Send upload failure notification
        send_notification(str(current_user.id), {
            "type": "upload_failed",
            "filename": file.filename,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )

@router.get("/presigned-url")
async def get_presigned_upload_url(
    filename: str,
    content_type: str = "application/octet-stream",
    current_user: User = Depends(get_current_user)
):
    """Get presigned URL for direct browser upload to S3"""
    
    if not allowed_file(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed"
        )
    
    org_id = current_user.organization or "default"
    
    try:
        presigned_data = await storage_service.get_presigned_upload_url(
            org_id=org_id,
            user_id=str(current_user.id),
            filename=filename,
            content_type=content_type
        )
        
        return presigned_data
        
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    
    # Find document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete from storage
        if document.s3_key and storage_service.storage_type == "s3":
            await storage_service.delete_file(document.s3_key)
        elif not document.s3_key:
            # Local file deletion
            local_path = Path("uploads") / document.filename
            if local_path.exists():
                local_path.unlink()
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        # Send deletion notification
        send_notification(str(current_user.id), {
            "type": "document_deleted",
            "filename": document.original_name,
            "document_id": document_id
        })
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user)
):
    """Get real-time notifications for current user"""
    user_id = str(current_user.id)
    user_notifications = notifications.get(user_id, [])
    
    # Clear notifications after reading
    if user_id in notifications:
        notifications[user_id] = []
    
    return {"notifications": user_notifications}

# Background task for document processing
async def process_document_async(document_id: str, file_content: bytes):
    """Process document asynchronously (extract text, generate preview, etc.)"""
    try:
        logger.info(f"Processing document {document_id} in background")
        # Here you would implement:
        # - Text extraction for searchability
        # - Thumbnail generation for images
        # - Metadata extraction
        # - Virus scanning
        # - AI analysis for compliance mapping
        
        # For now, just log completion
        await asyncio.sleep(2)  # Simulate processing
        logger.info(f"Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")

# Import asyncio for background processing
import asyncio