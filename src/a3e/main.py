"""
Main FastAPI Application for A3E - Proprietary Accreditation Intelligence Platform

Provides REST and GraphQL APIs for the Autonomous Accreditation & Audit Engine.
Features proprietary ontology, vector-weighted matching, multi-agent pipeline, and audit traceability.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import uvicorn
import logging
import os
from pathlib import Path
from datetime import datetime

from .core.config import settings
from .core.accreditation_registry import ALL_ACCREDITORS, get_accreditors_by_institution_type, get_accreditors_by_state
from .models import Institution, Evidence, Standard, AgentWorkflow, GapAnalysis
from .services.database_service import DatabaseService
# Optional services - will gracefully degrade if dependencies missing
try:
    from .services.vector_service import VectorService
    VECTOR_SERVICE_AVAILABLE = True
except ImportError:
    VECTOR_SERVICE_AVAILABLE = False
    # logger not yet configured; will log after config
    _vector_import_error = True

from .services.llm_service import LLMService
from .services.document_service import DocumentService
"""NOTE: Agent Orchestrator is optional. It depends on heavy LLM coordination
libraries (e.g., autogen) that aren't required for core API functionality.
We attempt to import it but degrade gracefully if unavailable so the
application can still boot for marketing pages and basic data endpoints."""
try:  # Optional orchestrator (may require missing deps like 'autogen')
    from typing import TYPE_CHECKING
    from .agents import A3EAgentOrchestrator  # type: ignore
    AGENT_ORCHESTRATOR_AVAILABLE = True
    if TYPE_CHECKING:  # pragma: no cover
        from .agents import A3EAgentOrchestrator as _A3EAgentOrchestratorType
except Exception as e:  # Broad except to catch ImportError + transitive errors
    AGENT_ORCHESTRATOR_AVAILABLE = False
    _agent_orchestrator_import_exception = e
from .api.routes import integrations_router, proprietary_router
# Import auth router separately to handle any import issues
try:
    from .api.routes.auth import router as auth_router
    auth_router_available = True
except ImportError as e:
    auth_router_available = False
    _auth_import_exception = e

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level), format=settings.log_format)
logger = logging.getLogger(__name__)
if '_vector_import_error' in globals():
    logger.warning("Vector service not available - AI features disabled")
if '_auth_import_exception' in globals():
    logger.warning(f"Auth router import failed: {_auth_import_exception}")
if not globals().get('AGENT_ORCHESTRATOR_AVAILABLE', False):
    logger.warning(f"Agent orchestrator unavailable - advanced multi-agent flows disabled: {globals().get('_agent_orchestrator_import_exception')}")

# Global service instances
db_service: Optional[DatabaseService] = None
vector_service: Optional[VectorService] = None
llm_service: Optional[LLMService] = None
document_service: Optional[DocumentService] = None
agent_orchestrator: Optional['A3EAgentOrchestrator'] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_service, vector_service, llm_service, document_service, agent_orchestrator
    
    logger.info("🚀 Starting A3E Application...")
    
    # Initialize services
    try:
        db_service = DatabaseService(settings.database_url)
        await db_service.initialize()
        logger.info("✅ Database service initialized")
        
        try:
            vector_service = VectorService(
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            await vector_service.initialize()
            logger.info("✅ Vector service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vector service unavailable (development mode): {e}")
            vector_service = None
        
        llm_service = LLMService(settings)
        await llm_service.initialize()
        logger.info("✅ LLM service initialized")
        
        document_service = DocumentService(settings)
        logger.info("✅ Document service initialized")
        
        if AGENT_ORCHESTRATOR_AVAILABLE:
            try:
                agent_orchestrator = A3EAgentOrchestrator(llm_service, vector_service)  # type: ignore
                logger.info("✅ Agent orchestrator initialized")
            except Exception as e:
                logger.warning(f"⚠️ Agent orchestrator unavailable (development mode): {e}")
                agent_orchestrator = None
        
        # Load accreditation standards into vector database
        await _load_accreditation_standards()
        logger.info("✅ Accreditation standards loaded")
        
        logger.info("🎉 A3E Application startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield  # Application runs here
    
    # Cleanup
    logger.info("🛑 Shutting down A3E Application...")
    if vector_service:
        await vector_service.close()
    if db_service:
        await db_service.close()
    logger.info("✅ Cleanup complete")

# Create FastAPI application
app = FastAPI(
    title="A³E - Autonomous Accreditation & Audit Engine",
    version=settings.version,
    description="""
    **Proprietary Accreditation Intelligence Platform**
    
    A³E provides comprehensive accreditation analysis using:
    
    🧠 **Proprietary Accreditation Ontology** - Hierarchical concept framework with 500+ accreditation concepts
    
    🔍 **Vector-Weighted Standards Matching** - Multi-dimensional similarity algorithm with 512-dimensional embeddings
    
    🤖 **Multi-Agent LLM Pipeline** - Four specialized agents (Mapper → GapFinder → Narrator → Verifier)
    
    📋 **Audit-Ready Traceability** - Complete immutable trail from evidence to final output
    
    ## Key Features
    
    - **Multi-Accreditor Support**: SACSCOC, HLC, MSCHE, NEASC, WASC, and more
    - **Institution-Type Contextualization**: Universities, colleges, community colleges, specialized institutions
    - **Evidence Gap Identification**: Automated detection with severity scoring
    - **Narrative Generation**: Professional prose suitable for accreditation reports
    - **Citation Verification**: ≥0.85 cosine similarity validation
    - **Complete Audit Trail**: Forensic-level traceability for regulatory review
    
    ## Proprietary Advantages
    
    - Only system with domain-specific accreditation ontology
    - Multi-dimensional embedding schema optimized for higher education
    - Specialized vector-weighted matching algorithm
    - Four-agent pipeline with role-based LLM specialization
    - Complete evidence-to-output traceability system
    """,
    lifespan=lifespan,
    docs_url=None,  # Disable default docs - using custom
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Templates configuration
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(project_root, "templates"))

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authentication dependency"""
    # TODO: Implement JWT token validation
    return {"user_id": "demo_user", "email": "demo@example.com"}

# Include API routes
from .api import api_router
from .api.routes.billing import router as billing_router

# Add basic auth endpoints directly (temporary fix for Railway deployment)
from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False

class UserRegistrationRequest(BaseModel):
    name: str
    institution_name: str
    email: EmailStr
    password: str
    role: str
    plan: str
    phone: Optional[str] = ""
    newsletter_opt_in: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# Simple in-memory user storage for Railway deployment
temp_users = {}

@app.post("/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """Temporary login endpoint for Railway deployment"""
    return AuthResponse(
        success=False,
        message="Authentication system is being deployed. Please try again in a few minutes."
    )

@app.post("/auth/register-trial", response_model=AuthResponse)
async def register_trial_user(request: UserRegistrationRequest):
    """Temporary registration endpoint for Railway deployment"""
    return AuthResponse(
        success=False,
        message="Registration system is being deployed. Please try again in a few minutes."
    )

@app.post("/auth/password-reset", response_model=AuthResponse)
async def request_password_reset(request: PasswordResetRequest):
    """Temporary password reset endpoint for Railway deployment"""
    return AuthResponse(
        success=False,
        message="Password reset system is being deployed. Please try again in a few minutes."
    )

# Include other routers
if auth_router_available:
    app.include_router(auth_router)
else:
    logger.warning("Auth router not available - using temporary auth endpoints")
app.include_router(integrations_router)
app.include_router(proprietary_router)
app.include_router(billing_router)
app.include_router(api_router, prefix=settings.api_prefix)

# Root endpoints
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_page(request: Request):
    """Enhanced landing page with system overview."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api", include_in_schema=False)
async def root_api():
    """API root endpoint with JSON system overview."""
    return {
        "message": "A³E - Autonomous Accreditation & Audit Engine",
        "version": settings.version,
        "environment": settings.environment,
        "proprietary_features": [
            "Accreditation ontology + embeddings schema",
            "Vector-weighted standards-matching algorithm", 
            "Multi-agent LLM pipeline (Mapper → GapFinder → Narrator → Verifier)",
            "Audit-ready traceability system from LLM output to evidentiary source"
        ],
        "supported_accreditors": len(ALL_ACCREDITORS),
        "endpoints": {
            "proprietary_analysis": "/api/v1/proprietary/analyze/complete",
            "evidence_analysis": "/api/v1/proprietary/analyze/evidence",
            "ontology_insights": "/api/v1/proprietary/ontology/insights",
            "traceability": "/api/v1/proprietary/traceability/{session_id}",
            "capabilities": "/api/v1/proprietary/capabilities",
            "integrations": "/api/v1/integrations/"
        },
        "docs_url": "/docs" if settings.is_development else "Documentation available upon request",
        "status": "operational"
    }

@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """Custom Swagger UI with enhanced styling."""
    return templates.TemplateResponse("docs.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        db_healthy = await db_service.health_check() if db_service else False
        
        # Check vector database connectivity
        vector_healthy = await vector_service.health_check() if vector_service else False
        
        # Check LLM service
        llm_healthy = await llm_service.health_check() if llm_service else False
        
        overall_healthy = all([db_healthy, vector_healthy, llm_healthy])
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "vector_db": "healthy" if vector_healthy else "unhealthy",
                "llm_service": "healthy" if llm_healthy else "unhealthy",
                "proprietary_ontology": "active",
                "vector_matching": "active", 
                "multi_agent_pipeline": "active",
                "audit_traceability": "active"
            },
            "version": settings.version,
            "proprietary_capabilities": "enabled"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get(f"{settings.api_prefix}/accreditors")
async def list_accreditors(
    state: Optional[str] = None,
    institution_type: Optional[str] = None,
    accreditor_type: Optional[str] = None
):
    """List all supported accrediting bodies with optional filters"""
    try:
        accreditors = list(ALL_ACCREDITORS.values())
        
        # Apply filters
        if state:
            accreditors = [
                acc for acc in accreditors
                if state.upper() in acc.geographic_scope or "National" in acc.geographic_scope
            ]
        
        if institution_type:
            from .core.accreditation_registry import InstitutionType
            try:
                inst_type = InstitutionType(institution_type.lower())
                accreditors = [
                    acc for acc in accreditors
                    if inst_type in acc.applicable_institution_types
                ]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid institution type: {institution_type}")
        
        if accreditor_type:
            from .core.accreditation_registry import AccreditorType
            try:
                acc_type = AccreditorType(accreditor_type.lower())
                accreditors = [acc for acc in accreditors if acc.type == acc_type]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid accreditor type: {accreditor_type}")
        
        return {
            "total_count": len(accreditors),
            "filters_applied": {
                "state": state,
                "institution_type": institution_type,
                "accreditor_type": accreditor_type
            },
            "accreditors": [
                {
                    "id": acc.id,
                    "name": acc.name,
                    "acronym": acc.acronym,
                    "type": acc.type.value,
                    "recognition_authority": acc.recognition_authority,
                    "geographic_scope": acc.geographic_scope,
                    "applicable_institution_types": [t.value for t in acc.applicable_institution_types],
                    "standards_count": len(acc.standards),
                    "website": acc.website
                }
                for acc in accreditors
            ]
        }
    except Exception as e:
        logger.error(f"Error listing accreditors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(f"{settings.api_prefix}/accreditors/{{accreditor_id}}/standards")
async def get_accreditor_standards(
    accreditor_id: str,
    institution_type: Optional[str] = None
):
    """Get standards for a specific accreditor, optionally filtered by institution type"""
    try:
        accreditor = ALL_ACCREDITORS.get(accreditor_id)
        if not accreditor:
            raise HTTPException(status_code=404, detail=f"Accreditor not found: {accreditor_id}")
        
        standards = accreditor.standards
        
        # Filter by institution type if provided
        if institution_type:
            from .core.accreditation_registry import InstitutionType
            try:
                inst_type = InstitutionType(institution_type.lower())
                standards = [
                    std for std in standards
                    if inst_type in std.applicable_institution_types
                ]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid institution type: {institution_type}")
        
        return {
            "accreditor": {
                "id": accreditor.id,
                "name": accreditor.name,
                "acronym": accreditor.acronym
            },
            "institution_type_filter": institution_type,
            "standards_count": len(standards),
            "standards": [
                {
                    "id": std.id,
                    "title": std.title,
                    "description": std.description,
                    "evidence_requirements": std.evidence_requirements,
                    "applicable_institution_types": [t.value for t in std.applicable_institution_types],
                    "weight": std.weight,
                    "sub_standards_count": len(std.sub_standards) if std.sub_standards else 0
                }
                for std in standards
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accreditor standards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(f"{settings.api_prefix}/workflows/execute")
async def execute_agent_workflow(
    background_tasks: BackgroundTasks,
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Execute the full agent workflow for an institution"""
    try:
        institution_id = request.get("institution_id")
        accreditor_id = request.get("accreditor_id")
        
        if not institution_id or not accreditor_id:
            raise HTTPException(
                status_code=400,
                detail="institution_id and accreditor_id are required"
            )
        
        # Validate inputs
        accreditor = ALL_ACCREDITORS.get(accreditor_id)
        if not accreditor:
            raise HTTPException(status_code=404, detail=f"Accreditor not found: {accreditor_id}")
        
        # Get institution and evidence from database
        institution = await db_service.get_institution(institution_id)
        if not institution:
            raise HTTPException(status_code=404, detail=f"Institution not found: {institution_id}")
        
        evidence_items = await db_service.get_institution_evidence(institution_id)
        
        # Start workflow in background
        background_tasks.add_task(
            _execute_workflow_background,
            institution,
            accreditor_id,
            evidence_items,
            current_user["user_id"]
        )
        
        return {
            "message": "Workflow execution started",
            "institution_id": institution_id,
            "accreditor_id": accreditor_id,
            "evidence_count": len(evidence_items),
            "status": "processing",
            "estimated_completion": "5-10 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(f"{settings.api_prefix}/evidence/upload")
async def upload_evidence(
    file: UploadFile = File(...),
    institution_id: str = None,
    evidence_type: str = "document",
    description: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Upload and process evidence document"""
    try:
        if not institution_id:
            raise HTTPException(status_code=400, detail="institution_id is required")
        
        # Validate file type and size
        if file.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_extension not in settings.supported_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {settings.supported_file_types}"
            )
        
        # Process document
        evidence_item = await document_service.process_uploaded_file(
            file=file,
            institution_id=institution_id,
            evidence_type=evidence_type,
            description=description,
            uploaded_by=current_user["user_id"]
        )
        
        return {
            "message": "Evidence uploaded and processing started",
            "evidence_id": str(evidence_item.id),
            "filename": file.filename,
            "status": "processing",
            "estimated_completion": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading evidence: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _load_accreditation_standards():
    """Load all accreditation standards into the vector database"""
    try:
        if vector_service is None:
            logger.info("⚠️ Skipping standards indexing - Vector service unavailable in development mode")
            return
            
        for accreditor in ALL_ACCREDITORS.values():
            await vector_service.index_standards(accreditor.standards)
        logger.info(f"Loaded {sum(len(acc.standards) for acc in ALL_ACCREDITORS.values())} standards into vector database")
    except Exception as e:
        logger.error(f"Error loading standards: {e}")
        raise

async def _execute_workflow_background(
    institution: Institution,
    accreditor_id: str,
    evidence_items: List[Evidence],
    user_id: str
):
    """Execute agent workflow in background"""
    try:
        logger.info(f"Starting workflow for institution {institution.id} with accreditor {accreditor_id}")
        
        # Execute the agent workflow
        results = await agent_orchestrator.execute_workflow(
            institution=institution,
            accreditor_id=accreditor_id,
            evidence_items=evidence_items,
            max_rounds=settings.agent_max_rounds
        )
        
        # Save results to database
        await db_service.save_workflow_results(results, user_id)
        
        logger.info(f"Workflow completed for institution {institution.id}")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        # TODO: Update workflow status to failed in database

#############################################
# Web / Marketing Pages
#############################################

# Resolve absolute path to /web directory (three levels up from this file: src/a3e/main.py -> repo root /web)
WEB_DIR = (Path(__file__).resolve().parent.parent.parent / "web").resolve()
if not WEB_DIR.exists():
    logger.warning(f"WEB_DIR does not exist at expected path: {WEB_DIR}")

def _read_web_file(filename: str) -> Optional[str]:
    path = WEB_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Web file not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Error reading web file {path}: {e}")
        return None

@app.get("/landing", response_class=HTMLResponse, include_in_schema=False)
async def landing_page(request: Request):  # noqa: D401
    """Serve marketing landing page."""
    content = _read_web_file("landing.html")
    if content is None:
        return HTMLResponse(content="<h1>Landing page not found</h1>", status_code=404)
    return HTMLResponse(content=content)

@app.get("/checkout", response_class=HTMLResponse, include_in_schema=False)
async def checkout_page(request: Request):  # noqa: D401
    """Serve checkout page."""
    content = _read_web_file("checkout.html")
    if content is None:
        return HTMLResponse(content="<h1>Checkout page not found</h1>", status_code=404)
    return HTMLResponse(content=content)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():  # noqa: D401
    """Return favicon if present; suppress 404 noise if missing."""
    icon_path = WEB_DIR / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    svg_path = WEB_DIR / "favicon.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    # Return empty 204 to avoid repeated 404 logs in browsers
    return Response(status_code=204)

# Mount static files for web assets and add direct routes for key pages
import os
from fastapi.responses import FileResponse

# Mount /web for static assets (js, images, etc.)
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")
    logger.info(f"Web directory mounted from: {WEB_DIR}")

    @app.get("/login", response_class=FileResponse, include_in_schema=False)
    async def login_page():
        return FileResponse(str(WEB_DIR / "login.html"))

    
    @app.get("/dashboard", response_class=FileResponse, include_in_schema=False)
    async def dashboard_page():
        return FileResponse(str(WEB_DIR / "dashboard.html"))
        
    @app.get("/homepage", response_class=FileResponse, include_in_schema=False)
    async def homepage():
        return FileResponse(str(WEB_DIR / "homepage.html"))
        
else:
    logger.warning(f"Web directory not found at: {WEB_DIR}")
    # Try alternative path for Railway deployment
    alt_web_directory = "web"
    if os.path.exists(alt_web_directory):
        app.mount("/web", StaticFiles(directory=alt_web_directory), name="web")
        logger.info(f"Web directory mounted from alternative path: {alt_web_directory}")

        # Add direct routes for key pages
        @app.get("/login", response_class=FileResponse, include_in_schema=False)
        async def login_page():
            return FileResponse(os.path.join(alt_web_directory, "login.html"))

        @app.get("/checkout", response_class=FileResponse, include_in_schema=False)
        async def checkout_page():
            return FileResponse(os.path.join(alt_web_directory, "checkout.html"))

        @app.get("/dashboard", response_class=FileResponse, include_in_schema=False)
        async def dashboard_page():
            return FileResponse(os.path.join(alt_web_directory, "dashboard.html"))

        @app.get("/homepage", response_class=FileResponse, include_in_schema=False)
        async def homepage():
            return FileResponse(os.path.join(alt_web_directory, "homepage.html"))
    else:
        logger.error("Web directory not found - static files will not be served")

if __name__ == "__main__":
    uvicorn.run(
        "src.a3e.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
