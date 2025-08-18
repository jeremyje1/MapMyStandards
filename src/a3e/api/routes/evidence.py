"""
Evidence API Routes for A3E

Provides REST endpoints for managing evidence documents and files.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import io

from ...core.config import settings
from ...services.database_service import DatabaseService
from ...services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class EvidenceCreate(BaseModel):
    title: str = Field(..., description="Evidence title")
    description: Optional[str] = Field(None, description="Evidence description")
    institution_id: str = Field(..., description="Institution ID")
    workflow_id: Optional[str] = Field(None, description="Associated workflow ID")
    evidence_type: str = Field(..., description="Type of evidence")
    tags: List[str] = Field(default_factory=list, description="Evidence tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class EvidenceResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    institution_id: str
    workflow_id: Optional[str]
    evidence_type: str
    tags: List[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    processed: bool
    extracted_text_preview: Optional[str]
    upload_date: str
    is_active: bool

class EvidenceDetail(EvidenceResponse):
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    institution_name: Optional[str]
    workflow_title: Optional[str]

class FileUploadResponse(BaseModel):
    evidence_id: str
    filename: str
    file_size: int
    mime_type: str
    processed: bool
    message: str

class ProcessingStatus(BaseModel):
    evidence_id: str
    processed: bool
    text_extracted: bool
    error_message: Optional[str]
    processing_time: Optional[float]

# Dependency for database service
async def get_db_service():
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()

# Dependency for document service
async def get_doc_service():
    return DocumentService()

@router.get("/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    institution_id: Optional[str] = Query(None, description="Filter by institution"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: DatabaseService = Depends(get_db_service)
):
    """List evidence with optional filters"""
    try:
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        evidence_list = await db.list_evidence(
            institution_id=institution_id,
            workflow_id=workflow_id,
            evidence_type=evidence_type,
            tags=tag_list,
            processed=processed,
            limit=limit,
            offset=offset
        )
        
        return [
            EvidenceResponse(
                id=str(ev.id),
                title=ev.title,
                description=ev.description,
                institution_id=str(ev.institution_id),
                workflow_id=str(ev.workflow_id) if ev.workflow_id else None,
                evidence_type=ev.evidence_type,
                tags=ev.tags,
                file_path=ev.file_path,
                file_size=ev.file_size,
                mime_type=ev.mime_type,
                processed=ev.processed,
                extracted_text_preview=ev.extracted_text[:200] + "..." if ev.extracted_text and len(ev.extracted_text) > 200 else ev.extracted_text,
                upload_date=ev.upload_date.isoformat(),
                is_active=ev.is_active
            )
            for ev in evidence_list
        ]
        
    except Exception as e:
        logger.error(f"Error listing evidence: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/evidence/{evidence_id}", response_model=EvidenceDetail)
async def get_evidence(
    evidence_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get detailed information about specific evidence"""
    try:
        evidence = await db.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Get related entities
        institution = await db.get_institution(str(evidence.institution_id))
        workflow = None
        if evidence.workflow_id:
            workflow = await db.get_workflow(str(evidence.workflow_id))
        
        return EvidenceDetail(
            id=str(evidence.id),
            title=evidence.title,
            description=evidence.description,
            institution_id=str(evidence.institution_id),
            workflow_id=str(evidence.workflow_id) if evidence.workflow_id else None,
            evidence_type=evidence.evidence_type,
            tags=evidence.tags,
            file_path=evidence.file_path,
            file_size=evidence.file_size,
            mime_type=evidence.mime_type,
            processed=evidence.processed,
            extracted_text_preview=evidence.extracted_text[:500] + "..." if evidence.extracted_text and len(evidence.extracted_text) > 500 else evidence.extracted_text,
            upload_date=evidence.upload_date.isoformat(),
            is_active=evidence.is_active,
            metadata=evidence.metadata,
            created_at=evidence.created_at.isoformat(),
            updated_at=evidence.updated_at.isoformat(),
            institution_name=institution.name if institution else None,
            workflow_title=workflow.title if workflow else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evidence", response_model=EvidenceDetail, status_code=201)
async def create_evidence(
    evidence_data: EvidenceCreate,
    db: DatabaseService = Depends(get_db_service)
):
    """Create new evidence record (without file)"""
    try:
        # Validate institution exists
        institution = await db.get_institution(evidence_data.institution_id)
        if not institution:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid institution ID: {evidence_data.institution_id}"
            )
        
        # Validate workflow if provided
        if evidence_data.workflow_id:
            workflow = await db.get_workflow(evidence_data.workflow_id)
            if not workflow:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid workflow ID: {evidence_data.workflow_id}"
                )
        
        # Create evidence
        evidence = await db.create_evidence(evidence_data.dict())
        
        return EvidenceDetail(
            id=str(evidence.id),
            title=evidence.title,
            description=evidence.description,
            institution_id=str(evidence.institution_id),
            workflow_id=str(evidence.workflow_id) if evidence.workflow_id else None,
            evidence_type=evidence.evidence_type,
            tags=evidence.tags,
            file_path=evidence.file_path,
            file_size=evidence.file_size,
            mime_type=evidence.mime_type,
            processed=evidence.processed,
            extracted_text_preview=None,
            upload_date=evidence.upload_date.isoformat(),
            is_active=evidence.is_active,
            metadata=evidence.metadata,
            created_at=evidence.created_at.isoformat(),
            updated_at=evidence.updated_at.isoformat(),
            institution_name=institution.name,
            workflow_title=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating evidence: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evidence/{evidence_id}/upload", response_model=FileUploadResponse)
async def upload_evidence_file(
    evidence_id: str,
    file: UploadFile = File(...),
    auto_process: bool = Form(True),
    db: DatabaseService = Depends(get_db_service),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Upload a file for existing evidence"""
    try:
        # Get evidence record
        evidence = await db.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        # Read file content
        file_content = await file.read()
        
        # Process file
        result = await doc_service.process_file(
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type
        )
        
        # Update evidence record
        update_data = {
            "file_path": result["file_path"],
            "file_size": result["file_size"],
            "mime_type": result["mime_type"],
            "processed": result["processed"],
            "extracted_text": result.get("extracted_text")
        }
        
        await db.update_evidence(evidence_id, update_data)
        
        return FileUploadResponse(
            evidence_id=evidence_id,
            filename=file.filename,
            file_size=result["file_size"],
            mime_type=result["mime_type"],
            processed=result["processed"],
            message="File uploaded and processed successfully" if result["processed"] else "File uploaded, processing may be needed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file for evidence {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evidence/upload", response_model=FileUploadResponse, status_code=201)
async def upload_evidence_with_file(
    title: str = Form(...),
    institution_id: str = Form(...),
    evidence_type: str = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    workflow_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    db: DatabaseService = Depends(get_db_service),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Create evidence and upload file in one operation"""
    try:
        # Validate institution
        institution = await db.get_institution(institution_id)
        if not institution:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid institution ID: {institution_id}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Read file content
        file_content = await file.read()
        
        # Process file
        result = await doc_service.process_file(
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type
        )
        
        # Create evidence with file info
        evidence_data = {
            "title": title,
            "description": description,
            "institution_id": institution_id,
            "workflow_id": workflow_id,
            "evidence_type": evidence_type,
            "tags": tag_list,
            "file_path": result["file_path"],
            "file_size": result["file_size"],
            "mime_type": result["mime_type"],
            "processed": result["processed"],
            "extracted_text": result.get("extracted_text"),
            "metadata": {"filename": file.filename}
        }
        
        evidence = await db.create_evidence(evidence_data)
        
        return FileUploadResponse(
            evidence_id=str(evidence.id),
            filename=file.filename,
            file_size=result["file_size"],
            mime_type=result["mime_type"],
            processed=result["processed"],
            message="Evidence created and file processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating evidence with file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/evidence/{evidence_id}/download")
async def download_evidence_file(
    evidence_id: str,
    db: DatabaseService = Depends(get_db_service),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Download the original evidence file"""
    try:
        evidence = await db.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        if not evidence.file_path:
            raise HTTPException(status_code=404, detail="No file associated with this evidence")
        
        # Get file content
        file_content = await doc_service.get_file_content(evidence.file_path)
        
        # Create streaming response
        file_stream = io.BytesIO(file_content)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=evidence.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={evidence.metadata.get('filename', f'evidence_{evidence_id}')}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading evidence file {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/evidence/{evidence_id}/text")
async def get_evidence_text(
    evidence_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get extracted text from evidence"""
    try:
        evidence = await db.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        if not evidence.extracted_text:
            raise HTTPException(status_code=404, detail="No extracted text available")
        
        return {
            "evidence_id": evidence_id,
            "title": evidence.title,
            "extracted_text": evidence.extracted_text,
            "character_count": len(evidence.extracted_text),
            "processed": evidence.processed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence text {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/evidence/{evidence_id}/process", response_model=ProcessingStatus)
async def process_evidence(
    evidence_id: str,
    force: bool = Query(False, description="Force reprocessing even if already processed"),
    db: DatabaseService = Depends(get_db_service),
    doc_service: DocumentService = Depends(get_doc_service)
):
    """Process or reprocess evidence file for text extraction"""
    try:
        evidence = await db.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        if not evidence.file_path:
            raise HTTPException(status_code=400, detail="No file associated with this evidence")
        
        if evidence.processed and not force:
            return ProcessingStatus(
                evidence_id=evidence_id,
                processed=True,
                text_extracted=bool(evidence.extracted_text),
                error_message=None,
                processing_time=0.0
            )
        
        # Reprocess file
        import time
        start_time = time.time()
        
        result = await doc_service.reprocess_file(evidence.file_path)
        
        processing_time = time.time() - start_time
        
        # Update evidence record
        update_data = {
            "processed": result["processed"],
            "extracted_text": result.get("extracted_text")
        }
        
        await db.update_evidence(evidence_id, update_data)
        
        return ProcessingStatus(
            evidence_id=evidence_id,
            processed=result["processed"],
            text_extracted=bool(result.get("extracted_text")),
            error_message=result.get("error"),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing evidence {evidence_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/evidence-types")
async def list_evidence_types(
    db: DatabaseService = Depends(get_db_service)
):
    """List all evidence types used in the system"""
    try:
        types = await db.get_evidence_types()
        
        return {
            "evidence_types": types,
            "total_count": len(types)
        }
        
    except Exception as e:
        logger.error(f"Error listing evidence types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/institutions/{institution_id}/evidence-summary")
async def get_institution_evidence_summary(
    institution_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get evidence summary for an institution"""
    try:
        # Validate institution
        institution = await db.get_institution(institution_id)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        summary = await db.get_institution_evidence_summary(institution_id)
        
        return {
            "institution_id": institution_id,
            "institution_name": institution.name,
            **summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence summary for {institution_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
