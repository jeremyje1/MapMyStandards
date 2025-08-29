"""
Report Generation API

Real report generation endpoints that create actual PDF reports
based on processed data, not demo placeholders.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...services.report_generation_service import get_report_service
from ...core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

settings = get_settings()


class ReportRequest(BaseModel):
    """Request model for report generation"""
    report_type: str  # comprehensive, gap_analysis, qep, evidence_mapping
    institution_id: str
    accreditor: Optional[str] = "SACSCOC"
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    include_recommendations: bool = True
    format: str = "pdf"  # pdf, docx, xlsx


class ReportResponse(BaseModel):
    """Response model for report generation"""
    report_id: str
    status: str
    message: str
    download_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReportStatus(BaseModel):
    """Status of report generation"""
    report_id: str
    status: str  # pending, generating, completed, failed
    progress: int  # 0-100
    message: str
    download_ready: bool
    error: Optional[str] = None


# In-memory storage for report jobs (should use Redis in production)
report_jobs = {}


async def generate_report_async(
    report_id: str,
    report_type: str,
    institution_id: str,
    parameters: Dict[str, Any]
):
    """
    Asynchronous report generation
    """
    try:
        # Update status
        report_jobs[report_id] = {
            "status": "generating",
            "progress": 10,
            "message": "Initializing report generation..."
        }
        
        # Get report service
        report_service = get_report_service()
        
        # Update progress
        report_jobs[report_id]["progress"] = 30
        report_jobs[report_id]["message"] = "Fetching institution data..."
        
        # Generate report
        report_jobs[report_id]["progress"] = 50
        report_jobs[report_id]["message"] = "Processing compliance data..."
        
        result = await report_service.generate_report(
            report_type=report_type,
            institution_id=institution_id,
            parameters=parameters
        )
        
        # Update final status
        report_jobs[report_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Report generated successfully",
            "file_path": result.get("file_path"),
            "metadata": result
        }
        
        logger.info(f"✅ Report {report_id} generated successfully")
        
    except Exception as e:
        logger.error(f"❌ Error generating report {report_id}: {e}")
        report_jobs[report_id] = {
            "status": "failed",
            "progress": 0,
            "message": "Report generation failed",
            "error": str(e)
        }


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a new compliance report
    
    This endpoint initiates real report generation based on actual processed data.
    Reports are generated asynchronously and can be downloaded when complete.
    """
    try:
        # Validate report type
        valid_types = ["comprehensive", "gap_analysis", "qep", "evidence_mapping"]
        if request.report_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report type. Must be one of: {valid_types}"
            )
        
        # Generate report ID
        import uuid
        report_id = str(uuid.uuid4())
        
        # Prepare parameters
        parameters = {
            "institution_id": request.institution_id,
            "accreditor": request.accreditor,
            "date_range_start": request.date_range_start,
            "date_range_end": request.date_range_end,
            "include_recommendations": request.include_recommendations,
            "format": request.format,
            "requested_at": datetime.utcnow().isoformat()
        }
        
        # Initialize job status
        report_jobs[report_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Report generation queued"
        }
        
        # Start background generation
        background_tasks.add_task(
            generate_report_async,
            report_id,
            request.report_type,
            request.institution_id,
            parameters
        )
        
        return ReportResponse(
            report_id=report_id,
            status="processing",
            message=f"{request.report_type.replace('_', ' ').title()} report generation started",
            download_url=None,
            metadata={
                "report_type": request.report_type,
                "institution_id": request.institution_id,
                "requested_at": parameters["requested_at"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating report generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{report_id}", response_model=ReportStatus)
async def get_report_status(report_id: str):
    """
    Get the status of a report generation job
    """
    if report_id not in report_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )
    
    job = report_jobs[report_id]
    
    return ReportStatus(
        report_id=report_id,
        status=job["status"],
        progress=job.get("progress", 0),
        message=job.get("message", "Unknown status"),
        download_ready=job["status"] == "completed",
        error=job.get("error")
    )


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """
    Download a generated report
    """
    if report_id not in report_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )
    
    job = report_jobs[report_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Status: {job['status']}"
        )
    
    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not found"
        )
    
    # Get report metadata
    metadata = job.get("metadata", {})
    report_type = metadata.get("report_type", "report")
    
    # Generate filename
    filename = f"{report_type}_report_{report_id[:8]}.pdf"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/list")
async def list_reports(
    institution_id: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, le=100)
):
    """
    List recent reports
    
    Returns real report data, not demo placeholders.
    """
    reports = []
    
    for report_id, job in list(report_jobs.items())[:limit]:
        metadata = job.get("metadata", {})
        
        # Apply filters
        if institution_id and metadata.get("institution_id") != institution_id:
            continue
        if report_type and metadata.get("report_type") != report_type:
            continue
        if status and job.get("status") != status:
            continue
        
        reports.append({
            "report_id": report_id,
            "report_type": metadata.get("report_type", "unknown"),
            "institution_id": metadata.get("institution_id"),
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "requested_at": metadata.get("requested_at"),
            "download_ready": job.get("status") == "completed"
        })
    
    return {"reports": reports, "total": len(reports)}


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a report and its associated file
    """
    if report_id not in report_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )
    
    job = report_jobs[report_id]
    
    # Delete file if it exists
    file_path = job.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting report file: {e}")
    
    # Remove from jobs
    del report_jobs[report_id]
    
    return {"message": f"Report {report_id} deleted successfully"}


@router.get("/metrics")
async def get_report_metrics(institution_id: str):
    """
    Get real metrics for an institution (not static demo data)
    
    This would normally query the database for actual processed data.
    For now, it calculates metrics based on jobs in memory.
    """
    # Count reports for this institution
    institution_reports = [
        job for job in report_jobs.values()
        if job.get("metadata", {}).get("institution_id") == institution_id
    ]
    
    # Calculate real metrics
    completed_reports = len([r for r in institution_reports if r.get("status") == "completed"])
    processing_reports = len([r for r in institution_reports if r.get("status") == "generating"])
    failed_reports = len([r for r in institution_reports if r.get("status") == "failed"])
    
    # These would come from the database in production
    metrics = {
        "institution_id": institution_id,
        "total_reports_generated": completed_reports,
        "reports_in_progress": processing_reports,
        "failed_reports": failed_reports,
        "compliance_score": 0.0,  # Would be calculated from actual data
        "documents_processed": 0,  # Would come from document processing
        "standards_mapped": 0,  # Would come from standards mapping
        "gaps_identified": 0,  # Would come from gap analysis
        "last_updated": datetime.utcnow().isoformat()
    }
    
    # If we have completed reports, extract some metrics
    if completed_reports > 0:
        # Get the most recent completed report
        latest_report = next(
            (job for job in institution_reports 
             if job.get("status") == "completed"),
            None
        )
        
        if latest_report and latest_report.get("metadata"):
            summary = latest_report["metadata"].get("summary", {})
            # Update with actual data if available
            if "compliance_score" in summary:
                metrics["compliance_score"] = summary["compliance_score"]
    
    return metrics