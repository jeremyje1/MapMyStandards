"""
Enhanced API routes for document storage, management, and report generation
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
import asyncio
import logging
import uuid
from datetime import datetime
import json

from ..services.database_service import DatabaseService
from ..services.document_service import DocumentService
from ..services.report_service import ReportService
from ..services.llm_service import LLMService
from ..core.config import settings
from ..models import Institution, Evidence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["document_management"])

# Service dependencies
async def get_db_service():
    db = DatabaseService(settings.database_url)
    await db.initialize()
    try:
        yield db
    finally:
        await db.close()

async def get_document_service():
    return DocumentService(settings)

async def get_report_service():
    llm_service = LLMService(settings)
    return ReportService(settings, llm_service)


@router.post("/upload", response_model=Dict[str, Any])
async def upload_documents(
    institution_id: str = Form(...),
    files: List[UploadFile] = File(...),
    evidence_types: Optional[str] = Form(None),  # JSON string of evidence types
    descriptions: Optional[str] = Form(None),    # JSON string of descriptions
    tags: Optional[str] = Form(None),           # JSON string of tags
    workflow_id: Optional[str] = Form(None),
    auto_analyze: bool = Form(True),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: DatabaseService = Depends(get_db_service),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Upload multiple documents with automatic processing and storage"""
    
    try:
        # Parse optional JSON parameters
        evidence_types_list = json.loads(evidence_types) if evidence_types else []
        descriptions_list = json.loads(descriptions) if descriptions else []
        tags_list = json.loads(tags) if tags else []
        
        uploaded_documents = []
        processing_tasks = []
        
        for i, file in enumerate(files):
            # Create evidence record
            evidence_type = evidence_types_list[i] if i < len(evidence_types_list) else "general"
            description = descriptions_list[i] if i < len(descriptions_list) else f"Uploaded document: {file.filename}"
            file_tags = tags_list[i] if i < len(tags_list) else []
            
            # Process document
            evidence = await doc_service.process_uploaded_file(
                file=file,
                institution_id=institution_id,
                evidence_type=evidence_type,
                description=description,
                uploaded_by="user"
            )
            
            uploaded_documents.append({
                "evidence_id": evidence.id,
                "filename": file.filename,
                "size": file.size,
                "type": evidence_type,
                "status": "processing"
            })
            
            # Add background analysis if requested
            if auto_analyze:
                background_tasks.add_task(
                    _analyze_document_background,
                    evidence.id,
                    institution_id,
                    db,
                    doc_service
                )
        
        return {
            "success": True,
            "upload_id": str(uuid.uuid4()),
            "documents": uploaded_documents,
            "total_uploaded": len(files),
            "auto_analyze": auto_analyze,
            "uploaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/library/{institution_id}", response_model=Dict[str, Any])
async def get_document_library(
    institution_id: str,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    evidence_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: DatabaseService = Depends(get_db_service)
):
    """Get paginated document library with search and filtering"""
    
    try:
        # Build query filters
        filters = {"institution_id": institution_id}
        if evidence_type:
            filters["evidence_type"] = evidence_type
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        # Get documents with pagination
        evidence_list = await db.get_evidence_paginated(
            filters=filters,
            search_query=search,
            page=page,
            page_size=page_size
        )
        
        # Calculate statistics
        total_count = await db.count_evidence(filters)
        total_size = await db.get_total_storage_size(institution_id)
        
        # Format response
        documents = []
        for evidence in evidence_list:
            documents.append({
                "id": evidence.id,
                "title": evidence.title,
                "filename": evidence.file_name,
                "type": evidence.evidence_type.value if evidence.evidence_type else "unknown",
                "size": evidence.file_size_bytes or 0,
                "uploaded_at": evidence.upload_date.isoformat() if evidence.upload_date else None,
                "processed_at": evidence.processed_at.isoformat() if evidence.processed_at else None,
                "status": evidence.processing_status.value if evidence.processing_status else "unknown",
                "relevance_score": evidence.relevance_score,
                "confidence_score": evidence.confidence_score,
                "keywords": evidence.keywords or [],
                "has_extracted_text": bool(evidence.extracted_text)
            })
        
        return {
            "documents": documents,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            },
            "statistics": {
                "total_documents": total_count,
                "total_storage_mb": round(total_size / (1024 * 1024), 2),
                "processed_documents": len([d for d in documents if d["status"] == "completed"]),
                "pending_documents": len([d for d in documents if d["status"] == "processing"])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get document library: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve library: {str(e)}")


@router.get("/search/{institution_id}", response_model=Dict[str, Any])
async def search_documents(
    institution_id: str,
    query: str,
    limit: int = 20,
    include_content: bool = False,
    db: DatabaseService = Depends(get_db_service)
):
    """Search documents by content, title, or keywords"""
    
    try:
        # Perform full-text search
        search_results = await db.search_evidence_content(
            institution_id=institution_id,
            search_query=query,
            limit=limit
        )
        
        results = []
        for evidence, relevance_score in search_results:
            result = {
                "id": evidence.id,
                "title": evidence.title,
                "filename": evidence.file_name,
                "type": evidence.evidence_type.value if evidence.evidence_type else "unknown",
                "relevance_score": relevance_score,
                "keywords": evidence.keywords or [],
                "snippet": evidence.extracted_text[:500] if evidence.extracted_text else evidence.description
            }
            
            if include_content:
                result["full_content"] = evidence.extracted_text
            
            results.append(result)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "searched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/reports/comprehensive", response_model=Dict[str, Any])
async def generate_comprehensive_report(
    institution_id: str = Form(...),
    accreditor_id: str = Form(...),
    report_type: str = Form("compliance_report"),
    include_evidence: bool = Form(True),
    include_narratives: bool = Form(True),
    additional_context: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate comprehensive accreditation report"""
    
    try:
        report_id = str(uuid.uuid4())
        
        # Start report generation in background
        background_tasks.add_task(
            _generate_report_background,
            report_id,
            institution_id,
            accreditor_id,
            report_type,
            include_evidence,
            include_narratives,
            additional_context,
            report_service
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "generating",
            "estimated_completion": "3-5 minutes",
            "report_type": report_type,
            "accreditor": accreditor_id,
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start report generation: {str(e)}")


@router.post("/reports/qep", response_model=Dict[str, Any])
async def generate_qep_report(
    institution_id: str = Form(...),
    qep_title: str = Form(...),
    qep_focus: str = Form(...),
    implementation_years: int = Form(5),
    assessment_data: Optional[str] = Form(None),  # JSON string
    additional_context: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate QEP impact and assessment report"""
    
    try:
        report_id = str(uuid.uuid4())
        
        # Parse QEP data
        qep_data = {
            "title": qep_title,
            "focus": qep_focus,
            "implementation_years": implementation_years,
            "assessment_data": json.loads(assessment_data) if assessment_data else {}
        }
        
        # Start QEP report generation in background
        background_tasks.add_task(
            _generate_qep_report_background,
            report_id,
            institution_id,
            qep_data,
            additional_context,
            report_service
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "generating",
            "qep_title": qep_title,
            "estimated_completion": "4-6 minutes",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"QEP report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start QEP report generation: {str(e)}")


@router.post("/narratives/generate", response_model=Dict[str, Any])
async def generate_narrative_responses(
    institution_id: str = Form(...),
    accreditor_id: str = Form(...),
    standard_ids: str = Form(...),  # JSON array of standard IDs
    evidence_ids: str = Form(...),  # JSON array of evidence IDs
    narrative_style: str = Form("formal"),
    additional_context: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate narrative responses for specific standards"""
    
    try:
        # Parse input arrays
        standard_ids_list = json.loads(standard_ids)
        evidence_ids_list = json.loads(evidence_ids)
        
        generation_id = str(uuid.uuid4())
        
        # Start narrative generation in background
        background_tasks.add_task(
            _generate_narratives_background,
            generation_id,
            institution_id,
            accreditor_id,
            standard_ids_list,
            evidence_ids_list,
            narrative_style,
            additional_context,
            report_service
        )
        
        return {
            "success": True,
            "generation_id": generation_id,
            "status": "generating",
            "standards_count": len(standard_ids_list),
            "evidence_count": len(evidence_ids_list),
            "style": narrative_style,
            "estimated_completion": "2-4 minutes",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Narrative generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start narrative generation: {str(e)}")


@router.get("/reports/{report_id}/status", response_model=Dict[str, Any])
async def get_report_status(
    report_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get status of report generation"""
    
    try:
        # Check report status in database
        report_status = await db.get_report_status(report_id)
        
        if not report_status:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "report_id": report_id,
            "status": report_status.get("status", "unknown"),
            "progress": report_status.get("progress", 0),
            "message": report_status.get("message", ""),
            "completed_at": report_status.get("completed_at"),
            "download_url": f"/api/v1/documents/reports/{report_id}/download" if report_status.get("status") == "completed" else None,
            "error_message": report_status.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = "pdf",  # pdf, docx, json
    db: DatabaseService = Depends(get_db_service)
):
    """Download generated report"""
    
    try:
        # Get report data
        report = await db.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Report not ready for download")
        
        # Generate file based on format
        if format == "json":
            return JSONResponse(content=report["data"])
        
        # For PDF/DOCX, we would generate the file here
        # For now, return the data as JSON
        return JSONResponse(content={
            "report_id": report_id,
            "format": format,
            "note": "File generation would be implemented here",
            "data": report["data"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# Background task functions

async def _analyze_document_background(
    evidence_id: str,
    institution_id: str,
    db: DatabaseService,
    doc_service: DocumentService
):
    """Analyze document in background"""
    try:
        # This would trigger the A³E analysis pipeline
        logger.info(f"Starting background analysis for evidence {evidence_id}")
        
        # Update status
        await db.update_evidence_status(evidence_id, "analyzing")
        
        # Simulate analysis (in real implementation, this would call the agent orchestrator)
        await asyncio.sleep(2)
        
        # Update completion status
        await db.update_evidence_status(evidence_id, "analyzed")
        
        logger.info(f"Completed background analysis for evidence {evidence_id}")
        
    except Exception as e:
        logger.error(f"Background analysis failed for {evidence_id}: {e}")
        await db.update_evidence_status(evidence_id, "failed", str(e))


async def _generate_report_background(
    report_id: str,
    institution_id: str,
    accreditor_id: str,
    report_type: str,
    include_evidence: bool,
    include_narratives: bool,
    additional_context: Optional[str],
    report_service: ReportService
):
    """Generate comprehensive report in background"""
    try:
        logger.info(f"Starting background report generation {report_id}")
        
        report_data = await report_service.generate_comprehensive_report(
            institution_id=institution_id,
            accreditor_id=accreditor_id,
            report_type=report_type,
            include_evidence=include_evidence,
            include_narratives=include_narratives,
            additional_context=additional_context
        )
        
        logger.info(f"Completed background report generation {report_id}")
        
    except Exception as e:
        logger.error(f"Background report generation failed for {report_id}: {e}")


async def _generate_qep_report_background(
    report_id: str,
    institution_id: str,
    qep_data: Dict[str, Any],
    additional_context: Optional[str],
    report_service: ReportService
):
    """Generate QEP report in background"""
    try:
        logger.info(f"Starting background QEP report generation {report_id}")
        
        report_data = await report_service.generate_qep_impact_report(
            institution_id=institution_id,
            qep_data=qep_data,
            additional_context=additional_context
        )
        
        logger.info(f"Completed background QEP report generation {report_id}")
        
    except Exception as e:
        logger.error(f"Background QEP report generation failed for {report_id}: {e}")


async def _generate_narratives_background(
    generation_id: str,
    institution_id: str,
    accreditor_id: str,
    standard_ids: List[str],
    evidence_ids: List[str],
    narrative_style: str,
    additional_context: Optional[str],
    report_service: ReportService
):
    """Generate narratives in background"""
    try:
        logger.info(f"Starting background narrative generation {generation_id}")
        
        narratives = []
        for standard_id in standard_ids:
            narrative = await report_service.generate_narrative_response(
                standard_id=standard_id,
                institution_id=institution_id,
                accreditor_id=accreditor_id,
                evidence_ids=evidence_ids,
                additional_context=additional_context,
                narrative_style=narrative_style
            )
            narratives.append(narrative)
        
        logger.info(f"Completed background narrative generation {generation_id}")
        
    except Exception as e:
        logger.error(f"Background narrative generation failed for {generation_id}: {e}")
