#!/usr/bin/env python3
"""
Simple trial server with just the working routes
Minimal FastAPI app to test the trial flow fixes
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from typing import Dict, Any, List, Optional
import uvicorn
import os
import json
import secrets
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Create app
app = FastAPI(
    title="MapMyStandards Trial Server",
    description="Simplified server for testing trial functionality",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Storage directories
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports_generated")
JOBS_DIR = Path("jobs_status")

# Create directories
for dir_path in [UPLOAD_DIR, REPORTS_DIR, JOBS_DIR]:
    dir_path.mkdir(exist_ok=True)

# In-memory storage
upload_store: Dict[str, Dict[str, Any]] = {}
report_store: Dict[str, Dict[str, Any]] = {}

# Mock authentication
async def get_current_user(credentials=Depends(security)):
    token = credentials.credentials
    if token in ["demo-token", "test-token"] or token.startswith("test-"):
        return {"user_id": f"user_{token[:8]}", "email": f"user_{token[:8]}@test.com"}
    return {"user_id": "demo_user", "email": "demo@mapmystandards.ai"}

# SACSCOC Standards Data
SACSCOC_STANDARDS = [
    {
        "id": "sacscoc_1_1", "accreditor": "SACSCOC", "code": "1.1", "title": "Mission",
        "description": "The institution has a clearly defined mission statement that articulates the institution's purpose, student population served, and commitment to student learning and student achievement.",
        "category": "Institutional Mission and Effectiveness", "parentId": None,
        "evidence_requirements": ["Mission Statement", "Board Approval Documentation", "Strategic Plan"],
        "is_required": True, "weight": 100
    },
    {
        "id": "sacscoc_2_1", "accreditor": "SACSCOC", "code": "2.1", "title": "Degree Standards",
        "description": "The institution offers one or more degree programs based on at least 60 semester credit hours or the equivalent at the baccalaureate level; at least 30 semester credit hours or the equivalent at the master's level.",
        "category": "Academic and Student Affairs", "parentId": None,
        "evidence_requirements": ["Degree Program Documentation", "Credit Hour Requirements", "Catalog Pages"],
        "is_required": True, "weight": 100
    },
    {
        "id": "sacscoc_8_1", "accreditor": "SACSCOC", "code": "8.1", "title": "Faculty",
        "description": "The institution employs a sufficient number of qualified faculty to support the mission of the institution and the goals of the degree programs.",
        "category": "Faculty", "parentId": None,
        "evidence_requirements": ["Faculty CVs", "Qualification Matrix", "Teaching Load Documentation"],
        "is_required": True, "weight": 100
    },
    {
        "id": "sacscoc_8_2_a", "accreditor": "SACSCOC", "code": "8.2.a", "title": "Faculty Evaluation",
        "description": "The institution regularly evaluates the effectiveness of each faculty member in accord with published criteria, regardless of contractual or employment terms.",
        "category": "Faculty", "parentId": "sacscoc_8_1",
        "evidence_requirements": ["Faculty Evaluation Process", "Evaluation Criteria", "Performance Reviews"],
        "is_required": True, "weight": 90
    },
    {
        "id": "sacscoc_9_1", "accreditor": "SACSCOC", "code": "9.1", "title": "Academic Support Services",
        "description": "The institution provides appropriate academic support services.",
        "category": "Academic and Student Affairs", "parentId": None,
        "evidence_requirements": ["Academic Support Services Documentation", "Tutoring Programs", "Advising Services"],
        "is_required": True, "weight": 85
    },
    {
        "id": "sacscoc_10_1", "accreditor": "SACSCOC", "code": "10.1", "title": "Financial Resources",
        "description": "The institution's recent financial history demonstrates financial stability with the capacity to support its programs and services.",
        "category": "Financial Resources", "parentId": None,
        "evidence_requirements": ["Audited Financial Statements", "Budget Documentation", "Revenue Analysis"],
        "is_required": True, "weight": 95
    },
    {
        "id": "sacscoc_11_1", "accreditor": "SACSCOC", "code": "11.1", "title": "Physical Resources",
        "description": "The institution's physical resources support student learning and the effective delivery of programs and services.",
        "category": "Physical Resources", "parentId": None,
        "evidence_requirements": ["Facilities Master Plan", "Campus Maps", "Safety Documentation"],
        "is_required": True, "weight": 80
    },
    {
        "id": "sacscoc_12_1", "accreditor": "SACSCOC", "code": "12.1", "title": "Resource Development",
        "description": "The institution has a sound financial base and demonstrated financial stability to support the mission of the institution and the scope of its programs and services.",
        "category": "Financial Resources", "parentId": None,
        "evidence_requirements": ["Fundraising Documentation", "Grant Records", "Endowment Reports"],
        "is_required": True, "weight": 75
    }
]

# Utility functions
def save_job_status(job_id: str, status_data: Dict[str, Any]):
    job_file = JOBS_DIR / f"{job_id}.json"
    with open(job_file, 'w') as f:
        json.dump(status_data, f, indent=2, default=str)
    upload_store[job_id] = status_data

def load_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    if job_id in upload_store:
        return upload_store[job_id]
    
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        with open(job_file, 'r') as f:
            status_data = json.load(f)
            upload_store[job_id] = status_data
            return status_data
    return None

def save_report_status(report_id: str, status_data: Dict[str, Any]):
    report_file = REPORTS_DIR / f"{report_id}_status.json"
    with open(report_file, 'w') as f:
        json.dump(status_data, f, indent=2, default=str)
    report_store[report_id] = status_data

def load_report_status(report_id: str) -> Optional[Dict[str, Any]]:
    if report_id in report_store:
        return report_store[report_id]
    
    report_file = REPORTS_DIR / f"{report_id}_status.json"
    if report_file.exists():
        with open(report_file, 'r') as f:
            status_data = json.load(f)
            report_store[report_id] = status_data
            return status_data
    return None

# Background tasks
async def simulate_document_analysis(job_id: str, filename: str):
    """Simulate document analysis with realistic progress steps"""
    steps = [
        ("extracting", "Extracting text from document", 10),
        ("parsing", "Parsing document structure", 25),
        ("embedding", "Generating content embeddings", 50),
        ("matching", "Matching against SACSCOC standards", 75),
        ("analyzing", "Computing gaps and coverage", 90),
        ("completed", "Analysis complete", 100)
    ]
    
    for step, description, progress in steps:
        status_data = load_job_status(job_id) or {}
        status_data.update({
            "status": step,
            "progress": progress,
            "description": description,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        if step == "completed":
            status_data.update({
                "results": {
                    "standards_matched": 8,
                    "total_standards": 12,
                    "confidence_score": 0.87,
                    "gaps_identified": 4,
                    "coverage_percentage": 67,
                    "mapped_standards": [
                        {"standard_id": "SACSCOC_1_1", "title": "Mission", "confidence": 0.92},
                        {"standard_id": "SACSCOC_2_1", "title": "Degree Standards", "confidence": 0.85},
                        {"standard_id": "SACSCOC_8_1", "title": "Faculty", "confidence": 0.78}
                    ]
                }
            })
        
        save_job_status(job_id, status_data)
        await asyncio.sleep(2)

async def generate_report_background(report_id: str, report_type: str):
    """Generate report in background"""
    # Update to generating
    status_data = load_report_status(report_id) or {}
    status_data.update({
        "status": "generating",
        "progress": 50,
        "message": "Generating report content",
        "updated_at": datetime.utcnow().isoformat()
    })
    save_report_status(report_id, status_data)
    
    await asyncio.sleep(3)  # Simulate report generation
    
    # Create mock PDF
    pdf_filename = f"{report_id}_{report_type}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename
    
    with open(pdf_path, 'w') as f:
        f.write(f"MapMyStandards {report_type.replace('_', ' ').title()} Report\n\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Report ID: {report_id}\n\n")
        f.write("This is a sample report demonstrating the working trial functionality.\n")
    
    # Mark as completed
    status_data.update({
        "status": "completed",
        "progress": 100,
        "message": "Report generated successfully",
        "pdf_filename": pdf_filename,
        "pdf_path": str(pdf_path),
        "download_url": f"/api/reports/{report_id}/download",
        "updated_at": datetime.utcnow().isoformat()
    })
    save_report_status(report_id, status_data)

# API Routes

@app.get("/")
async def root():
    return {
        "message": "MapMyStandards Trial Server", 
        "status": "operational",
        "endpoints": {
            "standards": "/api/standards",
            "uploads": "/api/uploads", 
            "reports": "/api/reports",
            "metrics": "/api/metrics/dashboard"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Standards API
@app.get("/api/standards")
async def list_standards(accreditor: Optional[str] = None):
    standards = SACSCOC_STANDARDS.copy()
    if accreditor and accreditor.upper() == "SACSCOC":
        pass  # Already filtered to SACSCOC
    
    return {
        "success": True,
        "message": "Standards retrieved successfully",
        "data": {
            "standards": standards,
            "total_count": len(standards),
            "last_updated": datetime.utcnow().isoformat()
        }
    }

# Upload API
@app.post("/api/uploads")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    # Validate file
    if not file.filename.endswith(('.txt', '.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Read and save file
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    # Generate IDs
    job_id = f"job_{secrets.token_hex(12)}"
    file_id = f"file_{secrets.token_hex(8)}"
    safe_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}.txt"
    
    # Save file
    file_path = UPLOAD_DIR / safe_filename
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create job record
    job_data = {
        "job_id": job_id,
        "file_id": file_id,
        "user_id": current_user["user_id"],
        "filename": file.filename,
        "safe_filename": safe_filename,
        "file_size": len(contents),
        "title": title or file.filename,
        "status": "queued",
        "progress": 0,
        "description": "Upload complete, analysis queued",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    save_job_status(job_id, job_data)
    
    # Start background analysis
    background_tasks.add_task(simulate_document_analysis, job_id, file.filename)
    
    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": "File uploaded successfully. Analysis started.",
            "data": {
                "job_id": job_id,
                "file_id": file_id,
                "filename": file.filename,
                "status": "queued"
            }
        }
    )

@app.get("/api/uploads/jobs/{job_id}")
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job_data = load_job_status(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True, "data": job_data}

# Reports API
@app.post("/api/reports")
async def generate_report(
    background_tasks: BackgroundTasks,
    report_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    report_type = report_request.get("type", "evidence_mapping_summary")
    report_id = f"rpt_{secrets.token_hex(12)}"
    
    report_data = {
        "report_id": report_id,
        "user_id": current_user["user_id"],
        "type": report_type,
        "status": "queued",
        "progress": 0,
        "message": "Report queued for generation",
        "created_at": datetime.utcnow().isoformat()
    }
    
    save_report_status(report_id, report_data)
    
    # Start background generation
    background_tasks.add_task(generate_report_background, report_id, report_type)
    
    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "message": "Report generation started",
            "data": {"report_id": report_id, "type": report_type, "status": "queued"}
        }
    )

@app.get("/api/reports/{report_id}")
async def get_report_status(report_id: str, current_user: dict = Depends(get_current_user)):
    report_data = load_report_status(report_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"success": True, "data": report_data}

@app.get("/api/reports/{report_id}/download")
async def download_report(report_id: str, current_user: dict = Depends(get_current_user)):
    report_data = load_report_status(report_id)
    if not report_data or report_data.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Report not ready")
    
    pdf_path = Path(report_data.get("pdf_path", ""))
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=str(pdf_path),
        filename=report_data.get("pdf_filename", "report.pdf"),
        media_type="application/pdf"
    )

# Metrics API
@app.get("/api/metrics/dashboard")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # Count user's jobs and reports
    user_jobs = [data for data in upload_store.values() if data.get("user_id") == user_id]
    user_reports = [data for data in report_store.values() if data.get("user_id") == user_id]
    
    documents_analyzed = len([j for j in user_jobs if j.get("status") == "completed"])
    reports_generated = len([r for r in user_reports if r.get("status") == "completed"])
    
    # Count standards mapped
    standards_mapped = set()
    for job in user_jobs:
        if job.get("status") == "completed" and job.get("results"):
            for std in job.get("results", {}).get("mapped_standards", []):
                standards_mapped.add(std.get("standard_id"))
    
    compliance_score = min(int((len(standards_mapped) / 12) * 100), 100) if standards_mapped else 0
    
    return {
        "success": True,
        "data": {
            "core_metrics": {
                "documents_analyzed": documents_analyzed,
                "standards_mapped": len(standards_mapped),
                "total_standards": 12,
                "reports_generated": reports_generated
            },
            "performance_metrics": {
                "compliance_score": compliance_score,
                "coverage_percentage": int((len(standards_mapped) / 12) * 100) if standards_mapped else 0
            },
            "account_info": {
                "is_trial": True,
                "trial_days_remaining": 11,
                "subscription_tier": "trial"
            }
        }
    }

# Serve static files from web directory
WEB_DIR = Path("web")
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory="web"), name="web")
    
    @app.get("/dashboard", response_class=FileResponse)
    async def dashboard():
        return FileResponse("web/dashboard.html")

if __name__ == "__main__":
    print("🚀 Starting MapMyStandards Trial Server")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔌 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "simple_trial_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )