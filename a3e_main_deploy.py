#!/usr/bin/env python3
"""
Simplified A3E Main Application for Production Deployment
Lightweight version with graceful degradation for missing dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
import uvicorn
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="A³E - Autonomous Accreditation & Audit Engine",
    description="AI-powered accreditation compliance and audit system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to include single-plan billing router so this lightweight entrypoint also supports checkout
try:  # pragma: no cover
    from src.a3e.api.routes.billing_single_plan import router as billing_single_plan_router
    from src.a3e.api.routes.billing_single_plan import legacy_single_plan_router as billing_single_plan_legacy_router
    app.include_router(billing_single_plan_router)
    app.include_router(billing_single_plan_legacy_router)
    logger.info("✅ Single-plan billing router loaded (deploy lightweight)")
except Exception as _e:  # pragma: no cover
    logger.warning(f"⚠️ Could not load single-plan billing router in deploy entrypoint: {_e}")

@app.get("/_sentinel_deploy", include_in_schema=False)
async def _sentinel_deploy():  # noqa: D401
    return {
        "entrypoint": "a3e_main_deploy",
        "single_plan_router": any(getattr(r, 'path', '').endswith('/create-single-plan-checkout') for r in app.router.routes),
        "route_count": len(app.router.routes)
    }

# Templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# Create directories if they don't exist
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files if directory exists
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global variables for services (graceful degradation)
db_service = None
vector_service = None
llm_service = None
agent_orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize services with graceful degradation"""
    global db_service, vector_service, llm_service, agent_orchestrator
    
    logger.info("🚀 Starting A³E Application...")
    
    # Try to initialize services, but don't fail if dependencies are missing
    try:
        # Database service (optional for demo)
        logger.info("⚠️  Database service: Using mock data (development mode)")
        
        # Vector service (optional)
        logger.info("⚠️  Vector service: Using mock search (development mode)")
        
        # LLM service (optional)
        logger.info("⚠️  LLM service: Using mock responses (development mode)")
        
        # Agent orchestrator (optional)
        logger.info("⚠️  Agent orchestrator: Using mock pipeline (development mode)")
        
        logger.info("✅ A³E Application started in development mode")
        
    except Exception as e:
        logger.warning(f"Service initialization warning: {e}")

@app.get("/")
async def root():
    """A3E Engine Home Page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>A³E - Autonomous Accreditation & Audit Engine</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
            .header { text-align: center; margin-bottom: 60px; }
            .header h1 { font-size: 3.5rem; margin: 0; font-weight: 700; }
            .header p { font-size: 1.3rem; margin: 20px 0; opacity: 0.9; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin: 40px 0; }
            .feature { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
            .feature h3 { margin: 0 0 15px 0; font-size: 1.4rem; }
            .cta { text-align: center; margin: 60px 0; }
            .btn { display: inline-block; padding: 15px 30px; background: #fff; color: #667eea; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px; transition: transform 0.2s; }
            .btn:hover { transform: translateY(-2px); }
            .status { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 A³E Engine</h1>
                <p>Autonomous Accreditation & Audit Engine</p>
                <p>AI-powered compliance analysis for educational institutions</p>
            </div>
            
            <div class="status">
                <h3>🚀 System Status</h3>
                <p>✅ A³E Engine: Online</p>
                <p>⚠️  AI Services: Development Mode</p>
                <p>⚠️  Vector Database: Mock Data</p>
                <p>📡 API Documentation: <a href="/docs" style="color: #fff;">Available</a></p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🎓 Dual-Mode Support</h3>
                    <p>Higher Education (SACSCOC, HLC, MSCHE) and K-12 (Cognia, AdvancED) accreditation standards.</p>
                </div>
                <div class="feature">
                    <h3>🤖 Multi-Agent Pipeline</h3>
                    <p>Mapper, GapFinder, Narrator, and Verifier agents work together for comprehensive analysis.</p>
                </div>
                <div class="feature">
                    <h3>📊 Real-Time Dashboards</h3>
                    <p>Interactive compliance dashboards with audit traceability and evidence mapping.</p>
                </div>
                <div class="feature">
                    <h3>🔒 Privacy Compliant</h3>
                    <p>FERPA and COPPA compliant processing with secure data handling.</p>
                </div>
            </div>
            
            <div class="cta">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/health" class="btn">🔍 System Health</a>
                <a href="/upload" class="btn">📄 Upload Documents</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "a3e-engine",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "mock" if not db_service else "active",
            "vector_search": "mock" if not vector_service else "active", 
            "llm": "mock" if not llm_service else "active",
            "agents": "mock" if not agent_orchestrator else "active"
        }
    }

@app.get("/upload")
async def upload_page():
    """Document upload interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>A³E - Document Upload</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
            h1 { color: #667eea; text-align: center; }
            .upload-area { border: 2px dashed #667eea; padding: 60px 20px; text-align: center; border-radius: 10px; margin: 20px 0; background: #f8f9ff; }
            .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #5a67d8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 Document Upload</h1>
            <div class="upload-area">
                <h3>🎯 Upload Institutional Documents</h3>
                <p>Drag and drop your accreditation documents here or click to browse</p>
                <p><small>Supported formats: PDF, DOCX, TXT</small></p>
                <input type="file" id="fileInput" multiple accept=".pdf,.docx,.txt" style="display: none;">
                <button class="btn" onclick="document.getElementById('fileInput').click()">Choose Files</button>
            </div>
            <div id="status" style="margin-top: 20px; padding: 20px; background: #e3f2fd; border-radius: 8px; display: none;">
                <h4>📊 Processing Status</h4>
                <p>⚠️ Demo Mode: File upload simulation only</p>
                <p>In production, this would:</p>
                <ul>
                    <li>Extract text and metadata from documents</li>
                    <li>Create vector embeddings for semantic search</li>
                    <li>Map content to accreditation standards</li>
                    <li>Generate compliance gap analysis</li>
                </ul>
            </div>
            <script>
                document.getElementById('fileInput').addEventListener('change', function(e) {
                    if (e.target.files.length > 0) {
                        document.getElementById('status').style.display = 'block';
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """)

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    results = []
    for file in files:
        # Mock processing for demo
        results.append({
            "filename": file.filename,
            "size": file.size if hasattr(file, 'size') else 0,
            "status": "processed",
            "standards_mapped": 12,
            "compliance_score": 85.6,
            "gaps_identified": 3
        })
    
    return {
        "message": f"Processed {len(files)} documents",
        "results": results,
        "demo_mode": True
    }

@app.get("/api/analysis/{document_id}")
async def get_analysis(document_id: str):
    """Get document analysis results"""
    # Mock analysis for demo
    return {
        "document_id": document_id,
        "compliance_score": 87.3,
        "standards_coverage": {
            "sacscoc": 92,
            "hlc": 84,
            "cognia": 78
        },
        "gaps": [
            {"standard": "SACSCOC 2.1", "severity": "medium", "description": "Student learning outcomes assessment"},
            {"standard": "HLC 3.A", "severity": "low", "description": "Faculty qualifications documentation"},
            {"standard": "Cognia 4.2", "severity": "high", "description": "Data-driven decision making evidence"}
        ],
        "recommendations": [
            "Enhance assessment documentation for learning outcomes",
            "Update faculty credentials database",
            "Implement systematic data collection processes"
        ],
        "demo_mode": True
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
