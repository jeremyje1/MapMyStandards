from typing import Dict
"""
Document upload and processing endpoints for A3E platform
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import uuid
import os
import logging

from ...models.user import User, UsageEvent
from ...services.database_service import DatabaseService
from ...services.document_service import DocumentService
from ...core.config import get_settings
from ..routes.auth_impl import verify_jwt_token

router = APIRouter(prefix="/api/documents", tags=["documents"])
security = HTTPBearer()
settings = get_settings()
logger = logging.getLogger(__name__)

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Auth dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    email = verify_jwt_token(token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Check trial status
    if user.is_trial and not user.is_trial_active:
        raise HTTPException(status_code=403, detail="Trial period has expired")
    
    return user


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document for analysis"""
    try:
        # Validate file type
        allowed_types = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )

        # Read file to get content and size
        contents = await file.read()
        file_size = len(contents)

        # Check file size (max from settings)
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )

        # Generate unique filename
        document_id = str(uuid.uuid4())
        safe_filename = f"{document_id}{file_ext}"

        # Create upload directory if it doesn't exist
        upload_base = getattr(settings, "data_dir", "/app/data")
        upload_dir = os.path.join(upload_base, "uploads", str(current_user.get("id")))
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, safe_filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Track usage event
        usage_event = UsageEvent(
            user_id=current_user.get("id"),
            event_type="document_upload",
            event_data={
                "category": "analysis",
                "filename": file.filename,
                "file_size": file_size,
                "file_type": file_ext,
                "document_id": document_id
            }
        )
        db.add(usage_event)
        
        # Update user stats
        current_user.documents_analyzed += 1
        
        await db.commit()
        
        # Queue document for processing
        background_tasks.add_task(
            process_document,
            document_id,
            file_path,
            current_user.get("id"),
            file.filename
        )
        
        logger.info(f"Document uploaded: {document_id} by user {current_user.get("email")}")
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "filename": file.filename,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload document"
        )


async def process_document(document_id: str, file_path: str, user_id: str, original_filename: str):
    """Process uploaded document in background"""
    try:
        # Initialize document service
        doc_service = DocumentService(settings)
        
        # Extract text and analyze
        logger.info(f"Processing document {document_id}")
        
        # TODO: Implement actual document processing
        # This would include:
        # 1. Text extraction
        # 2. Accreditation standard mapping
        # 3. Compliance scoring
        # 4. Evidence identification
        
        # For now, just log
        logger.info(f"Document {document_id} processing queued")
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")


@router.get("/list")
async def list_documents(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's uploaded documents"""
    try:
        # TODO: Implement proper document listing from database
        # For now, return mock data based on user stats
        
        documents = []
        if current_user.documents_analyzed > 0:
            # Generate some mock documents
            for i in range(min(current_user.documents_analyzed, 5)):
                documents.append({
                    "id": str(uuid.uuid4()),
                    "filename": f"Sample Document {i+1}.pdf",
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "status": "completed",
                    "compliance_score": 85 + i * 2,
                    "standards_mapped": 12 + i
                })
        
        return {
            "success": True,
            "documents": documents,
            "total": current_user.documents_analyzed
        }
        
    except Exception as e:
        logger.error(f"Document list error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get document details and analysis results"""
    try:
        # TODO: Implement actual document retrieval
        # For now, return mock data
        
        return {
            "success": True,
            "document": {
                "id": document_id,
                "filename": "Sample Curriculum Document.pdf",
                "uploaded_at": datetime.utcnow().isoformat(),
                "status": "completed",
                "analysis": {
                    "compliance_score": 87,
                    "standards_mapped": 15,
                    "gaps_identified": 3,
                    "recommendations": [
                        "Add more detail about assessment methods",
                        "Include learning outcomes mapping",
                        "Specify faculty qualifications"
                    ]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Document retrieval error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    try:
        # TODO: Implement actual document deletion
        # This should remove:
        # 1. The file from storage
        # 2. Database records
        # 3. Any associated analysis results
        
        # Track usage event
        usage_event = UsageEvent(
            user_id=current_user.get("id"),
            event_type="document_delete",
            event_category="analysis",
            event_metadata={"document_id": document_id}
        )
        db.add(usage_event)
        await db.commit()
        
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Document deletion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document"
        )
