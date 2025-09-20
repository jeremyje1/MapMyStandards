"""
Secure file upload API with cloud storage support (S3 presigned preferred).
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...models.document import Document
from ...services.database_service import DatabaseService
from ...services.storage_service import StorageService, get_storage_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

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
    "text/csv",
]


class PresignRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)
    size: int = Field(..., gt=0, le=MAX_FILE_SIZE)


class PresignResponse(BaseModel):
    upload_url: str
    upload_fields: Dict[str, Any]
    file_key: str
    expires_in: int


class CompleteUploadRequest(BaseModel):
    file_key: str
    filename: str
    size: int
    content_type: str
    hash: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    file_key: Optional[str] = None
    download_url: Optional[str] = None


async def get_db():
    settings = get_settings()
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session


def _extract_user_info(user: Any) -> Dict[str, str]:
    try:
        user_id = getattr(user, "id", None)
        email = getattr(user, "email", None)
        org = getattr(user, "institution_name", None) or getattr(user, "org", None)
    except Exception:
        user_id = None
        email = None
        org = None
    if isinstance(user, dict):
        user_id = user_id or user.get("user_id") or user.get("sub")
        email = email or user.get("email") or user.get("sub")
        org = org or user.get("institution_name") or user.get("org")
    return {
        "user_id": str(user_id or (email or "anon")[:12] or "anon"),
        "org_id": str(org or "default"),
        "email": str(email or ""),
    }


@router.post("/presign", response_model=PresignResponse)
async def get_presigned_upload_url(
    request: PresignRequest,
    current_user: Any = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
):
    # Validate content type
    if request.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Supported types: PDF, Word, Excel, PowerPoint, Text, CSV",
        )
    # Validate file size
    if request.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    try:
        info = _extract_user_info(current_user)
        presign_data = await storage.get_presigned_upload_url(
            org_id=info["org_id"],
            user_id=info["user_id"],
            filename=request.filename,
            content_type=request.content_type,
            max_size=request.size,
        )

        return PresignResponse(
            upload_url=presign_data["url"],
            upload_fields=presign_data.get("fields", {}),
            file_key=presign_data["key"],
            expires_in=presign_data["expires_in"],
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL",
        )


@router.post("/complete", response_model=UploadResponse)
async def complete_upload(
    request: CompleteUploadRequest,
    current_user: Any = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db),
):
    info = _extract_user_info(current_user)
    # Special-case demo token: skip DB writes to avoid FK constraints
    if info["user_id"] == "demo_user":
        try:
            download_url = await storage.get_download_url(
                file_key=request.file_key, filename=request.filename
            )
        except Exception:
            download_url = None
        return UploadResponse(
            success=True,
            message="File upload recorded (demo mode; metadata not persisted)",
            file_id=None,
            file_key=request.file_key,
            download_url=download_url,
        )

    try:
        document = Document(
            user_id=info["user_id"],
            filename=request.filename,
            file_key=request.file_key,
            content_type=request.content_type,
            file_size=request.size,
            sha256=request.hash,
            uploaded_at=datetime.utcnow(),
            status="uploaded",
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        download_url = await storage.get_download_url(
            file_key=request.file_key, filename=request.filename
        )

        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=str(document.id),
            file_key=request.file_key,
            download_url=download_url,
        )
    except Exception as e:
        logger.error(f"Failed to complete upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save upload metadata",
        )


@router.post("/direct", response_model=UploadResponse)
async def upload_file_direct(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db),
):
    # Validate content type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Supported types: PDF, Word, Excel, PowerPoint, Text, CSV",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    try:
        info = _extract_user_info(current_user)
        file_key = storage.generate_file_key(
            org_id=info["org_id"], user_id=info["user_id"], filename=file.filename
        )

        save_result = await storage.save_file(
            file_content=content,
            file_key=file_key,
            content_type=file.content_type,
            metadata={
                "original_name": file.filename,
                "user_id": info["user_id"],
                "uploaded_at": datetime.utcnow().isoformat(),
            },
        )

        document = Document(
            user_id=info["user_id"],
            filename=file.filename,
            file_key=file_key,
            content_type=file.content_type,
            file_size=save_result["size"],
            sha256=save_result["hash"],
            uploaded_at=datetime.utcnow(),
            status="uploaded",
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        download_url = await storage.get_download_url(
            file_key=file_key, filename=file.filename
        )

        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=str(document.id),
            file_key=file_key,
            download_url=download_url,
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )


@router.get("/files")
async def list_user_files(
    current_user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    info = _extract_user_info(current_user)
    # Demo token: return empty set without DB access
    if info["user_id"] == "demo_user":
        return {"files": []}

    try:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == info["user_id"])  
            .order_by(Document.uploaded_at.desc())
            .limit(limit)
        )
        documents = result.scalars().all()

        return {
            "files": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "size": doc.file_size,
                    "content_type": doc.content_type,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "status": doc.status,
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files",
        )


@router.get("/download/{file_key}")
async def download_file(
    file_key: str,
    current_user: Any = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        info = _extract_user_info(current_user)
        result = await db.execute(
            select(Document)
            .where(Document.file_key == file_key)
            .where(Document.user_id == info["user_id"])
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        content = await storage.get_file(file_key)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not found",
            )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=document.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename}"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file",
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Any = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        info = _extract_user_info(current_user)
        result = await db.execute(
            select(Document)
            .where(Document.id == file_id)
            .where(Document.user_id == info["user_id"])
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        await storage.delete_file(document.file_key)
        await db.delete(document)
        await db.commit()

        return {"success": True, "message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )
