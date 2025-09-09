"""
Main FastAPI Application for A3E - Proprietary Accreditation Intelligence Platform

Provides REST and GraphQL APIs for the Autonomous Accreditation & Audit Engine.
Features proprietary ontology, vector-weighted matching, multi-agent pipeline, and audit traceability.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request, Response
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import uvicorn
import logging
import os
import tempfile
import os.path
from pathlib import Path
from datetime import datetime

# Local imports
from .services.llm_service import LLMService
from .services.document_service import DocumentService
from .api.routes import integrations_router, proprietary_router
from .services.analytics_service import analytics_service

# Configure basic logging first before any imports that might use it  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporarily comment out problematic imports for debugging
try:
    from .core.config import settings
    # Reconfigure logging with proper settings after config is loaded
    logging.basicConfig(level=getattr(logging, settings.log_level), format=settings.log_format)
    logger = logging.getLogger(__name__)
    logger.info("✅ Config imported successfully")
except Exception as e:
    logger.error(f"❌ Config import failed: {e}")
    raise

try:
    from .core.accreditation_registry import ALL_ACCREDITORS, get_accreditors_by_institution_type, get_accreditors_by_state
    logger.info("✅ Accreditation registry imported successfully")
except Exception as e:
    logger.error(f"❌ Accreditation registry import failed: {e}")
    ALL_ACCREDITORS = {}

try:
    from .models import Institution, Evidence, Standard, AgentWorkflow, GapAnalysis
    logger.info("✅ Models imported successfully")
except Exception as e:
    logger.error(f"❌ Models import failed: {e}")

try:
    from .services.database_service import DatabaseService
    logger.info("✅ Database service imported successfully")
except Exception as e:
    logger.error(f"❌ Database service import failed: {e}")
    DatabaseService = None

try:
    from .api import api_router
    logger.info("✅ API router imported successfully")
except Exception as e:
    logger.error(f"❌ API router import failed: {e}")
    api_router = None

try:
    from .api.routes.billing import router as billing_router
    logger.info("✅ Billing router imported successfully")
except Exception as e:
    logger.error(f"❌ Billing router import failed: {e}")
    billing_router = None
try:
    from .api.routes.onboarding import router as onboarding_router
    _onboarding_available = True
except Exception as _e:
    _onboarding_available = False
try:
    from .api.routes.billing import legacy_router as billing_legacy_router  # type: ignore
    _billing_legacy_available = True
except Exception:
    _billing_legacy_available = False
# Optional services - will gracefully degrade if dependencies missing
try:
    # Check if we should use Pinecone or Milvus
    if os.environ.get("VECTOR_DB_PROVIDER") == "pinecone":
        from .services.pinecone_service import PineconeVectorService as VectorService
        VECTOR_SERVICE_AVAILABLE = True
        USING_PINECONE = True
    else:
        from .services.vector_service import VectorService
        VECTOR_SERVICE_AVAILABLE = True
        USING_PINECONE = False
except ImportError:
    VECTOR_SERVICE_AVAILABLE = False
    USING_PINECONE = False
    # logger not yet configured; will log after config
    _vector_import_error = True

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
# Import auth router separately to handle any import issues
try:
    from .api.routes.auth_db import router as auth_router
    auth_router_available = True
except ImportError as e:
    auth_router_available = False
    _auth_import_exception = e

# Import new routers
try:
    from .api.routes.trial import router as trial_router
    trial_router_available = True
except ImportError as e:
    trial_router_available = False
    _trial_import_exception = e

try:
    from .api.routes.auth_impl import router as auth_impl_router
    auth_impl_router_available = True
except ImportError as e:
    auth_impl_router_available = False

try:
    from .api.routes.narrative_generation import router as narrative_router
    narrative_router_available = True
except ImportError as e:
    narrative_router_available = False
    _auth_impl_import_exception = e

try:
    from .api.routes.documents import router as documents_router
    from .api.routes.documents import upload_document as upload_document_handler
    documents_router_available = True
except ImportError as e:
    documents_router_available = False
    _documents_import_exception = e

try:
    from .api.routes.dashboard import router as dashboard_router
    dashboard_router_available = True
except ImportError as e:
    dashboard_router_available = False
    _dashboard_import_exception = e

try:
    from .api.routes.compliance import router as compliance_router
    compliance_router_available = True
except ImportError as e:
    compliance_router_available = False
    _compliance_import_exception = e

try:
    from .api.routes.auth_complete import router as auth_complete_router
    auth_complete_router_available = True
except ImportError as e:
    auth_complete_router_available = False
    _auth_complete_import_exception = e

try:
    from .api.routes.auth_simple import router as auth_simple_router
    auth_simple_router_available = True
except ImportError as e:
    auth_simple_router_available = False
    _auth_simple_import_exception = e

# Session-based auth (access + refresh cookies)
try:
    from .api.routes.auth_session import router as auth_session_router
    auth_session_router_available = True
except ImportError as e:
    auth_session_router_available = False
    _auth_session_import_exception = e

# Single plan billing (hosted Stripe Checkout) router
try:
    from .api.routes.billing_single_plan import router as billing_single_plan_router
    from .api.routes.billing_single_plan import legacy_single_plan_router as billing_single_plan_legacy_router
    billing_single_plan_router_available = True
except ImportError as e:
    billing_single_plan_router_available = False
    _billing_single_plan_import_exception = e

try:
    from .api.routes.upload import router as upload_router
    upload_router_available = True
except ImportError as e:
    upload_router_available = False
    _upload_import_exception = e

try:
    from .api.routes.evidence_mappings import router as evidence_mappings_router
    evidence_mappings_router_available = True
except ImportError as e:
    evidence_mappings_router_available = False
    _evidence_mappings_import_exception = e

try:
    from .api.routes.analytics import router as analytics_router
    analytics_router_available = True
except ImportError as e:
    analytics_router_available = False
    _analytics_import_exception = e

try:
    from .api.routes.email_test import router as email_test_router
    email_test_router_available = True
except ImportError as e:
    email_test_router_available = False
    _email_test_import_exception = e

try:
    from .api.routes.ai_status import router as ai_status_router
    ai_status_router_available = True
except ImportError as e:
    ai_status_router_available = False
    _ai_status_import_exception = e

try:
    from .api.routes.db_init import router as db_init_router
    db_init_router_available = True
except ImportError as e:
    db_init_router_available = False
    _db_init_import_exception = e

# Compliance Intelligence Router
try:
    from .api.routes.compliance_intelligence import router as intelligence_router
    intelligence_router_available = True
except ImportError as e:
    intelligence_router_available = False
    _intelligence_import_exception = e

# Password Reset Router
try:
    from .api.routes.password_reset import router as password_reset_router
    password_reset_router_available = True
except ImportError as e:
    password_reset_router_available = False
    _password_reset_import_exception = e

# Logging already configured at top of file

# Optional strict asset enforcement (set STRICT_FRONTEND_ASSETS=1 to fail startup if missing)
STRICT_FRONTEND_ASSETS = os.getenv("STRICT_FRONTEND_ASSETS", "0").lower() in ("1", "true", "yes")

# Cross-worker warning deduplication using filesystem

def log_warning_once_global(message: str, key: str = None):
    """Log warning once across all workers using filesystem marker"""
    if key is None:
        key = message[:50]  # Use first 50 chars as key
    marker_file = os.path.join(tempfile.gettempdir(), f"a3e_warning_{hash(key) % 10000}.tmp")
    if not os.path.exists(marker_file):
        try:
            with open(marker_file, 'w') as f:
                f.write(message)
            logger.warning(message)
        except OSError:
            # Fallback to regular logging if filesystem issues
            logger.warning(message)

# One-time warning logger to avoid duplicate noise within worker
_LOGGED_WARNINGS = set()
def log_warning_once(message: str):  # pragma: no cover - simple helper
    if message not in _LOGGED_WARNINGS:
        _LOGGED_WARNINGS.add(message)
        log_warning_once_global(message)

if '_vector_import_error' in globals():
    log_warning_once("Vector service not available - AI features disabled")
if '_auth_import_exception' in globals():
    log_warning_once(f"Auth router import failed: {_auth_import_exception}")
if not globals().get('AGENT_ORCHESTRATOR_AVAILABLE', False):
    log_warning_once(f"Agent orchestrator unavailable - advanced multi-agent flows disabled: {globals().get('_agent_orchestrator_import_exception')}")

# Global service instances
db_service: Any = None
vector_service: Any = None
llm_service: Any = None
document_service: Any = None
agent_orchestrator: Any = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_service, vector_service, llm_service, document_service, agent_orchestrator
    
    logger.info("🚀 Starting A3E Application...")
    # Record startup time for uptime calculations
    app.state.start_time = datetime.utcnow()
    
    # Initialize services
    try:
        # Initialize production database
        try:
            from .database.connection import db_manager
            await db_manager.initialize()
            logger.info("✅ Production database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Production database init failed: {e}")
            # Fallback to legacy database service
            try:
                db_service = DatabaseService(settings.database_url)
                await db_service.initialize()
                logger.info("✅ Legacy database service initialized (fallback)")
            except Exception as e2:
                logger.error(f"❌ All database initialization failed: {e2}")
                db_service = None
        
        # Ensure database schema is created (especially for SQLite)
        try:
            from sqlalchemy import create_engine
            from .models import Base
            
            engine = create_engine(settings.database_url)
            Base.metadata.create_all(engine)
            engine.dispose()
            logger.info("✅ Database schema verified/created")
        except Exception as e:
            logger.warning(f"⚠️ Database schema creation failed: {e}")
        
        try:
            if VECTOR_SERVICE_AVAILABLE:
                if USING_PINECONE:
                    # Initialize Pinecone service
                    vector_service = VectorService()  # PineconeVectorService takes no args
                    if await vector_service.initialize():
                        logger.info("✅ Pinecone vector service initialized")
                    else:
                        logger.warning("⚠️ Pinecone initialization failed - check API key")
                        vector_service = None
                else:
                    # Initialize Milvus service
                    vector_service = VectorService(
                        host=settings.milvus_host,
                        port=settings.milvus_port
                    )
                    await vector_service.initialize()
                    logger.info("✅ Milvus vector service initialized")
            else:
                log_warning_once("⚠️ Vector service unavailable - missing dependencies")
                vector_service = None
        except Exception as e:
            log_warning_once(f"⚠️ Vector service unavailable: {str(e)}")
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
                log_warning_once(f"⚠️ Agent orchestrator unavailable (development mode): {str(e)}")
                agent_orchestrator = None
        else:
            log_warning_once("⚠️ Agent orchestrator unavailable - missing dependencies (autogen)")
            agent_orchestrator = None

        # Verify Tailwind build presence (non-fatal unless STRICT_FRONTEND_ASSETS enabled)
        try:
            css_path = WEB_DIR / "static" / "css" / "tailwind.css"
            css_issue = None
            if not css_path.exists():
                css_issue = f"missing at {css_path}"
            else:
                size = css_path.stat().st_size
                if size < 5000:
                    css_issue = f"suspiciously small ({size} bytes)"
            if css_issue:
                msg = f"[frontend-assets] tailwind.css {css_issue}"
                if settings.is_production and STRICT_FRONTEND_ASSETS:
                    logger.error(msg + " (STRICT mode - aborting startup)")
                    raise RuntimeError(msg)
                else:
                    logger.warning(msg + " (degraded mode; CDN fallback will be used)")
                    app.state.tailwind_degraded = True  # type: ignore[attr-defined]
            else:
                logger.info("Tailwind CSS OK (size=%s bytes)", css_path.stat().st_size)
        except Exception as css_err:
            # Only fatal if strict
            if settings.is_production and STRICT_FRONTEND_ASSETS:
                raise
            logger.error(f"Non-fatal frontend asset verification error: {css_err}")

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
    
    # Close production database
    try:
        from .database.connection import db_manager
        await db_manager.close()
        logger.info("✅ Production database closed")
    except Exception as e:
        logger.error(f"❌ Production database cleanup error: {e}")
    
    # Close legacy services
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

# Add CORS middleware (parse comma-separated env var properly)
_cors_origins: list[str] = []
try:
    if isinstance(settings.cors_origins, str):
        _cors_origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
    else:  # type: ignore
        _cors_origins = list(settings.cors_origins)  # type: ignore
except Exception:
    _cors_origins = []

# Ensure platform + api domains are allowed (idempotent append)
for required_origin in [
    "https://platform.mapmystandards.ai",
    "https://api.mapmystandards.ai",
    "https://mapmystandards.ai",
    "https://www.mapmystandards.ai",
    "https://app.mapmystandards.ai",  # React app on Railway
    "http://localhost:8000",
    "http://localhost:3000",  # React dev server
    "http://localhost:3001",  # Alternative React port
    "http://localhost:8888",  # Local static server / alt dev port
]:
    if required_origin not in _cors_origins:
        _cors_origins.append(required_origin)

if not _cors_origins:
    _cors_origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)
logger.info("CORS configured allow_origins=%s", _cors_origins)

# Security
security = HTTPBearer()

# Templates configuration
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(project_root, "templates"))

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authentication dependency with basic JWT validation"""
    try:
        token = credentials.credentials
        # For now, accept demo tokens for testing
        if token == "demo-token" or token.startswith("test-"):
            return {"user_id": "demo_user", "email": "demo@example.com"}
        
        # Basic validation - in production, use proper JWT library
        if len(token) < 20:
            raise HTTPException(status_code=401, detail="Invalid token format")
            
        # Extract email from token payload (simplified for demo)
        # In production, properly decode and validate JWT
        return {
            "user_id": token[:8],  # First 8 chars as user ID
            "email": f"user_{token[:8]}@mapmystandards.ai"
        }
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

class LoginRequest(BaseModel):  # Temporary inline models
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

# Include authentication routers
# Commented out conflicting auth routers - using auth_simple instead
# if auth_router_available:
#     app.include_router(auth_router)
#     logger.info("✅ Auth router loaded")
# else:
#     logger.warning("⚠️ Auth router not available - authentication disabled")

# Include new routers
if trial_router_available:
    app.include_router(trial_router)
    logger.info("✅ Trial router loaded")
else:
    logger.warning("⚠️ Trial router not available")

# Include customer experience routers
try:
    from .api.routes.sample_data import router as sample_data_router
    app.include_router(sample_data_router)
    logger.info("✅ Sample data router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Sample data router not available: {e}")

try:
    from .api.routes.nurturing import router as nurturing_router
    app.include_router(nurturing_router)
    logger.info("✅ Email nurturing router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Email nurturing router not available: {e}")

# Commented out - using auth_simple instead
# if auth_impl_router_available:
#     app.include_router(auth_impl_router)
#     logger.info("✅ Auth implementation router loaded")
# else:
#     logger.warning("⚠️ Auth implementation router not available")

if documents_router_available:
    app.include_router(documents_router)
    logger.info("✅ Documents router loaded")
    # Back-compat aliases (frontend uses /documents/*)
    try:
        # Only add if not already registered
        existing = [r.path for r in app.router.routes if hasattr(r, 'path')]
        if "/documents/upload" not in existing:
            app.add_api_route("/documents/upload", upload_document_handler, methods=["POST"])
            logger.info("🔗 Added alias route: POST /documents/upload -> /api/documents/upload")
        else:
            logger.info("ℹ️ Alias route /documents/upload already present")

        # Temporary debug route to verify alias in prod (safe, GET only, no data)
        async def documents_upload_debug():
            return {"status": "ok", "message": "documents upload endpoint available"}

        if "/documents/upload/debug" not in existing:
            app.add_api_route("/documents/upload/debug", documents_upload_debug, methods=["GET"])
    except Exception as e:
        logger.warning(f"⚠️ Could not add alias route for documents upload: {e}")
else:
    logger.warning("⚠️ Documents router not available")

if dashboard_router_available:
    app.include_router(dashboard_router)
    logger.info("✅ Dashboard router loaded")
else:
    logger.warning("⚠️ Dashboard router not available")

if compliance_router_available:
    app.include_router(compliance_router)
    logger.info("✅ Compliance router loaded")
else:
    logger.warning("⚠️ Compliance router not available")

# Use auth_complete for registration endpoints but rename to avoid conflicts
if auth_complete_router_available:
    app.include_router(auth_complete_router)
    logger.info("✅ Auth complete router loaded")
else:
    logger.warning("⚠️ Auth complete router not available")

# Add the simple auth router that actually works
if auth_simple_router_available:
    app.include_router(auth_simple_router)
    logger.info("✅ Simple auth router loaded")
else:
    logger.warning("⚠️ Simple auth router not available")

if 'auth_session_router_available' in globals() and auth_session_router_available:
    app.include_router(auth_session_router)
    logger.info("✅ Session auth router loaded (access + refresh cookies)")
else:
    logger.warning("⚠️ Session auth router not available")

# Mount single plan billing checkout endpoints (hosted Stripe Checkout flow)
if 'billing_single_plan_router_available' in globals() and billing_single_plan_router_available:
    app.include_router(billing_single_plan_router)
    logger.info("✅ Single-plan billing router loaded (hosted checkout)")
    try:
        app.include_router(billing_single_plan_legacy_router)
        logger.info("✅ Single-plan legacy router loaded (/api/billing/*)")
    except Exception as _e:
        logger.warning(f"⚠️ Could not mount legacy single-plan router: {_e}")
    # Extra diagnostic log to confirm environment price configuration (masked)
    try:
        import os as _os
        _price_id = _os.getenv("STRIPE_SINGLE_PLAN_PRICE_ID") or _os.getenv("STRIPE_PRICE_MONTHLY") or "<unset>"
        if _price_id and _price_id not in ("<unset>"):
            _masked = _price_id[:6] + "..." + _price_id[-4:]
        else:
            _masked = _price_id
        logger.info(f"🔍 Single-plan price env detected: {_masked}")
    except Exception as _e:  # pragma: no cover - best effort
        logger.warning(f"⚠️ Could not log single-plan price env: {_e}")
else:
    logger.warning("⚠️ Single-plan billing router not available")

# Sentinel route very early for deployment verification (confirm this file is active)
@app.get("/_sentinel_main", include_in_schema=False)
async def _sentinel_main():  # noqa: D401
    return {
        "entrypoint": "src.a3e.main",
        "billing_single_plan_router_available": bool(globals().get("billing_single_plan_router_available")),
        "billing_single_plan_routes_present": any(
            getattr(r, 'path', '').endswith('/create-single-plan-checkout') for r in app.router.routes
        ),
        "total_routes": len(app.router.routes)
    }

@app.get("/__sentinel", include_in_schema=False)
async def _sentinel_simple():  # noqa: D401
    return {"ok": True, "ts": __import__('datetime').datetime.utcnow().isoformat() + 'Z'}

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
    _prom_enabled = True
    REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['method', 'path', 'status'])
    CHECKOUT_SESSIONS = Counter('checkout_sessions_created_total', 'Checkout sessions created')
    FALLBACK_PROVISION = Counter('fallback_provision_created_total', 'Fallback user provisions created')
    VERIFY_LATENCY = Histogram('verify_session_latency_seconds', 'Latency for verify-session handler')
except Exception:
    _prom_enabled = False

@app.middleware("http")
async def _metrics_middleware(request, call_next):  # type: ignore
    if not _prom_enabled:
        return await call_next(request)
    from time import time
    start = time()
    response = await call_next(request)
    try:
        REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
    except Exception:
        pass
    # Specialized counters updated inside billing router via logging (optional future wiring)
    if request.url.path.endswith('/create-single-plan-checkout') and response.status_code < 500:
        try:
            CHECKOUT_SESSIONS.inc()
        except Exception:
            pass
    if request.url.path.endswith('/verify-session') and response.status_code == 200:
        # Histogram only for verify-session
        try:
            VERIFY_LATENCY.observe(time() - start)
        except Exception:
            pass
    return response

@app.get('/metrics', include_in_schema=False)
async def metrics():  # noqa: D401
    if not _prom_enabled:
        return Response("prometheus_client not installed", status_code=503)
    data = generate_latest()  # type: ignore
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/robots.txt", include_in_schema=False)
async def robots():  # noqa: D401
    # Explicitly allow all so external services cannot claim blocking.
    return Response(content="User-agent: *\nDisallow:\n", media_type="text/plain")

if narrative_router_available:
    app.include_router(narrative_router)
    logger.info("✅ Narrative generation router loaded")
else:
    logger.warning("⚠️ Narrative generation router not available")

if upload_router_available:
    app.include_router(upload_router)
    logger.info("✅ Upload router loaded")
else:
    logger.warning("⚠️ Upload router not available")

if evidence_mappings_router_available:
    app.include_router(evidence_mappings_router)
    logger.info("✅ Evidence mappings router loaded")
else:
    logger.warning("⚠️ Evidence mappings router not available")

if analytics_router_available:
    app.include_router(analytics_router)
    logger.info("✅ Analytics router loaded")
else:
    logger.warning("⚠️ Analytics router not available")

if email_test_router_available:
    app.include_router(email_test_router)
    logger.info("✅ Email test router loaded")
else:
    logger.warning("⚠️ Email test router not available")

if ai_status_router_available:
    app.include_router(ai_status_router)
    logger.info("✅ AI status router loaded")
else:
    logger.warning("⚠️ AI status router not available")

if db_init_router_available:
    app.include_router(db_init_router)
    logger.info("✅ Database init router loaded")
else:
    logger.warning("⚠️ Database init router not available")

# Include database-powered routers (production-ready)
try:
    from .api.routes.uploads_db import router as uploads_db_router
    app.include_router(uploads_db_router)
    logger.info("✅ Database uploads router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Database uploads router not available: {e}")
    # Fallback to file-based
    try:
        from .api.routes.uploads_fixed import router as uploads_fixed_router
        app.include_router(uploads_fixed_router)
        logger.info("✅ File-based uploads router loaded (fallback)")
    except ImportError as e2:
        logger.error(f"❌ No uploads router available: {e2}")

try:
    from .api.routes.reports_db import router as reports_db_router
    app.include_router(reports_db_router)
    logger.info("✅ Database reports router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Database reports router not available: {e}")
    # Fallback to file-based
    try:
        from .api.routes.reports import router as reports_router
        app.include_router(reports_router)
        logger.info("✅ File-based reports router loaded (fallback)")
    except ImportError as e2:
        logger.error(f"❌ No reports router available: {e2}")

try:
    from .api.routes.metrics_db import router as metrics_db_router
    app.include_router(metrics_db_router)
    logger.info("✅ Database metrics router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Database metrics router not available: {e}")
    # Fallback to file-based
    try:
        from .api.routes.metrics import router as metrics_router
        app.include_router(metrics_router)
        logger.info("✅ File-based metrics router loaded (fallback)")
    except ImportError as e2:
        logger.error(f"❌ No metrics router available: {e2}")

try:
    from .api.routes.standards_db import router as standards_db_router
    app.include_router(standards_db_router)
    logger.info("✅ Database standards router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Database standards router not available: {e}")
    # Fallback to mock
    try:
        from .api.routes.standards_mock import router as standards_mock_router
        app.include_router(standards_mock_router)
        logger.info("✅ Mock standards router loaded (fallback)")
    except ImportError as e2:
        logger.error(f"❌ No standards router available: {e2}")

# Include Compliance Intelligence router
if intelligence_router_available:
    app.include_router(intelligence_router)
    logger.info("✅ Compliance Intelligence router loaded")
else:
    logger.warning(f"⚠️ Compliance Intelligence router not available")

# Include Password Reset router
if password_reset_router_available:
    app.include_router(password_reset_router)
    logger.info("✅ Password Reset router loaded")
else:
    logger.warning(f"⚠️ Password Reset router not available")

# Include Enhanced Auth router (with JWT and cookies)
try:
    from .api.routes.auth_enhanced import router as auth_enhanced_router
    app.include_router(auth_enhanced_router)
    logger.info("✅ Enhanced Auth router loaded (JWT + cookies)")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced Auth router not available: {e}")

# Include S3 Upload router
try:
    from .api.routes.upload import router as s3_upload_router
    app.include_router(s3_upload_router)
    logger.info("✅ S3 Upload router loaded (presigned URLs)")
except ImportError as e:
    logger.warning(f"⚠️ S3 Upload router not available: {e}")
    # Try local storage fallback
    try:
        from .api.routes.upload_local import router as local_upload_router
        app.include_router(local_upload_router)
        logger.info("✅ Local Upload router loaded (fallback)")
    except ImportError as e2:
        logger.warning(f"⚠️ No upload router available: {e2}")

# Include Personalization router
try:
    from .api.routes.personalization import router as personalization_router
    app.include_router(personalization_router)
    logger.info("✅ Personalization router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Personalization router not available: {e}")

# Include routers with error handling
try:
    app.include_router(integrations_router)
    logger.info("✅ Integrations router included")
except Exception as e:
    logger.error(f"❌ Integrations router failed: {e}")

try:
    app.include_router(proprietary_router)  
    logger.info("✅ Proprietary router included")
except Exception as e:
    logger.error(f"❌ Proprietary router failed: {e}")

if billing_router:
    try:
        app.include_router(billing_router)
        logger.info("✅ Billing router included")
    except Exception as e:
        logger.error(f"❌ Billing router failed: {e}")

if _billing_legacy_available:
    try:
        app.include_router(billing_legacy_router)
        logger.info("✅ Billing legacy router included")
    except Exception as e:
        logger.error(f"❌ Billing legacy router failed: {e}")

if _onboarding_available:
    try:
        app.include_router(onboarding_router)
        logger.info("✅ Onboarding router included")
    except Exception as e:
        logger.error(f"❌ Onboarding router failed: {e}")

if api_router:
    try:
        app.include_router(api_router, prefix=settings.api_prefix)
        logger.info("✅ API router included")
    except Exception as e:
        logger.error(f"❌ API router failed: {e}")

# Import and include customer pages router
try:
    from .routes import upload_api as lightweight_upload_api
    app.include_router(lightweight_upload_api.router)
    logger.info("✅ Lightweight upload_api router loaded (placeholder)")
except Exception as e:
    logger.warning(f"⚠️ Could not load lightweight upload_api router: {e}")

# Real document processing with AI
try:
    from .api.routes.document_processing import router as document_processing_router
    app.include_router(document_processing_router)
    logger.info("✅ Document processing router loaded (AI-powered)")
except Exception as e:
    logger.warning(f"⚠️ Could not load document processing router: {e}")

# Real report generation
try:
    from .api.routes.report_generation import router as report_generation_router
    app.include_router(report_generation_router)
    logger.info("✅ Report generation router loaded (real reports)")
except Exception as e:
    logger.warning(f"⚠️ Could not load report generation router: {e}")

# Root-level WebSocket endpoint for frontend clients: wss://api.../ws
@app.websocket("/ws")
async def websocket_root(ws: WebSocket):
    """WebSocket endpoint bridging to analytics real-time service.

    Auth: supports optional `token` and `user_id` query params.
    If absent, a demo user_id is used to allow public dashboard previews.
    """
    params = ws.query_params
    token = params.get("token")
    user_id = params.get("user_id") or "demo"

    # Env toggle to allow demo fallback (default OFF in production)
    demo_mode = os.getenv("DASHBOARD_DEMO_MODE", "0").lower() in ("1", "true", "yes", "y")

    if not demo_mode:
        # In non-demo mode, require a plausible token
        if not token or len(token) < 10:
            await ws.close(code=4401)
            return

    try:
        # Register connection (register_connection will accept the socket)
        await analytics_service.register_connection(ws, user_id)
        while True:
            try:
                message = await ws.receive_text()
                if message == "ping":
                    await ws.send_text("pong")
            except WebSocketDisconnect:
                break
    finally:
        try:
            await analytics_service.unregister_connection(user_id)
        except Exception:
            pass

# Define health endpoint BEFORE customer_pages router to avoid catch-all interference
@app.get("/health")
async def health_check():
    """Comprehensive health/status endpoint with per-service diagnostics.

    Returns structured JSON containing:
      - overall status (healthy / degraded / unhealthy)
      - per-service status + optional latency metrics
      - uptime and versioning metadata
    """
    try:
        from time import perf_counter
        now = datetime.utcnow()
        uptime_seconds = None
        if hasattr(app.state, 'start_time'):
            uptime_seconds = (now - app.state.start_time).total_seconds()

        # Helper to measure latency of async call returning bool
        async def timed(check_coro):
            start = perf_counter()
            try:
                ok = await check_coro
            except Exception:
                ok = False
            duration_ms = round((perf_counter() - start) * 1000, 2)
            return ok, duration_ms

        # Check if services are initialized (during startup they might be None)
        db_ok, db_latency = (False, None)
        # Try production db_manager first, fallback to legacy db_service
        try:
            from .database.connection import db_manager
            if db_manager and db_manager._initialized:
                db_ok, db_latency = await timed(db_manager.health_check())
        except:
            pass
        
        if not db_ok and db_service:
            db_ok, db_latency = await timed(db_service.health_check())

        vector_status = "unavailable"
        vector_ok = False
        vector_latency = None
        if vector_service:
            vector_ok, vector_latency = await timed(vector_service.health_check())
            vector_status = "healthy" if vector_ok else "unhealthy"

        llm_ok, llm_latency = (False, None)
        if llm_service:
            llm_ok, llm_latency = await timed(llm_service.health_check())

        orchestrator_status = "unavailable"
        if agent_orchestrator:
            # Simple heartbeat attribute/method optional
            orchestrator_status = "healthy"

        # Determine overall status: 
        # - If no services initialized yet (startup), return "starting"
        # - If core services (db) available, determine healthy/degraded/unhealthy
        # Check if either db_manager or db_service is available
        db_available = False
        try:
            from .database.connection import db_manager
            db_available = db_manager and db_manager._initialized
        except:
            pass
        if not db_available:
            db_available = db_service is not None
            
        if not db_available:
            overall = "starting"
            status_code = 200  # Allow health checks during startup
        else:
            core_services_ok = all([db_ok, llm_ok])
            degraded = core_services_ok and not all([vector_ok, orchestrator_status == "healthy"])
            if core_services_ok and not degraded:
                overall = "healthy"
            elif core_services_ok and degraded:
                overall = "degraded"
            else:
                overall = "unhealthy"
            status_code = 200 if overall in ("healthy", "degraded") else 503

        body: Dict[str, Any] = {
            "status": overall,
            "timestamp": now.isoformat(),
            "uptime_seconds": uptime_seconds,
            "version": settings.version,
            "environment": settings.environment,
            "services": {
                "database": {"status": "healthy" if db_ok else ("unavailable" if not db_service else "unhealthy"), "latency_ms": db_latency},
                "llm_service": {"status": "healthy" if llm_ok else ("unavailable" if not llm_service else "unhealthy"), "latency_ms": llm_latency},
                "vector_db": {"status": vector_status, "latency_ms": vector_latency},
                "agent_orchestrator": {"status": orchestrator_status}
            },
            "capabilities": {
                "proprietary_ontology": True,
                "vector_matching": vector_ok,
                "multi_agent_pipeline": orchestrator_status == "healthy",
                "audit_traceability": True
            }
        }

        if overall == "degraded":
            body["note"] = "Core services healthy. Optional advanced services unavailable or unhealthy."
        elif overall == "starting":
            body["note"] = "Application starting up. Services initializing."
            
        return JSONResponse(status_code=status_code, content=body)
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

try:
    from .routes.customer_pages import router as customer_pages_router
    app.include_router(customer_pages_router)
    logger.info("✅ Customer pages router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Customer pages router not available: {e}")

# Import and include reports implementation router
try:
    from .api.routes.reports_impl import router as reports_impl_router
    app.include_router(reports_impl_router)
    logger.info("✅ Reports implementation router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Reports implementation router not available: {e}")

# Import and include analytics router
try:
    from .api.routes.analytics import router as analytics_router
    app.include_router(analytics_router)
    logger.info("✅ Analytics router loaded")
except ImportError as e:
    logger.warning(f"⚠️ Analytics router not available: {e}")

# Import and include tier router
try:
    from src.a3e.api.routes.tier import router as tier_router
    app.include_router(tier_router)
    logger.info("✅ Tier management router loaded")
except ImportError:
    logger.warning("⚠️ Tier router not available")

# Root endpoints
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_page(request: Request):
    """Root marketing page.

    Always try to serve /web/index.html (committed static marketing page).
    Previously this attempted customer_homepage.html first then a Jinja template
    which does not exist in templates/, leading to 404s in production. We remove
    the template dependency to make the root deterministic.
    """
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        logger.info("[root] Serving index.html from web directory (%s)", index_file)
        return FileResponse(str(index_file))
    
    # Try homepage.html as fallback
    homepage_file = WEB_DIR / "homepage.html"
    if homepage_file.exists():
        logger.info("[root] Fallback to homepage.html from web directory (%s)", homepage_file)
        return FileResponse(str(homepage_file))
    
    # As a last resort, redirect users to the trial signup page
    logger.warning("[root] Both index.html (%s) and homepage.html missing - redirecting to /trial-signup", index_file)
    return HTMLResponse("<html><head><meta http-equiv='refresh' content='0; url=/trial-signup'></head><body>Redirecting...</body></html>")

# Lightweight debug endpoint to confirm static asset presence (not in schema)
@app.get("/debug/static", response_class=JSONResponse, include_in_schema=False)
async def debug_static():
    css_path = WEB_DIR / "static" / "css" / "tailwind.css"
    return {
        "tailwind_exists": css_path.exists(),
        "tailwind_size": css_path.stat().st_size if css_path.exists() else None,
        "web_dir": str(WEB_DIR),
        "listed_files_sample": sorted([p.name for p in WEB_DIR.glob("*.html")])[:20]
    }

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

@app.get("/health/frontend")
async def frontend_health():
    """Report presence & size of critical frontend assets (CSS, logo, core JS)."""
    assets = []
    
    def assess(path: Path, name: str, min_bytes: int) -> dict:
        exists = path.exists()
        size = path.stat().st_size if exists else None
        status = "healthy" if exists and size and size >= min_bytes else ("degraded" if exists else "missing")
        return {
            "name": name,
            "path": str(path),
            "exists": exists,
            "size_bytes": size,
            "min_threshold": min_bytes,
            "status": status,
        }
    css_path = WEB_DIR / "static" / "css" / "tailwind.css"
    assets.append(assess(css_path, "tailwind.css", 5000))
    # Common logo filenames (first existing reported)
    logo_candidates = [
        WEB_DIR / "static" / "img" / "logo.png",
        WEB_DIR / "static" / "img" / "logo.svg",
        WEB_DIR / "static" / "img" / "logo-dark.png",
    ]
    for lc in logo_candidates:
        if lc.exists():
            assets.append(assess(lc, lc.name, 500))
            break
    core_js = WEB_DIR / "js" / "a3e-sdk.js"
    assets.append(assess(core_js, "a3e-sdk.js", 200))
    overall = "healthy"
    if any(a["status"] == "missing" for a in assets):
        overall = "missing"
    elif any(a["status"] == "degraded" for a in assets):
        overall = "degraded"
    return {
        "status": overall,
        "assets": assets,
        "timestamp": datetime.utcnow().isoformat()
    }

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

# Resolve absolute path to /web directory
# In Docker/Railway, we're at /app, so web is at /app/web
# In local dev, we're at src/a3e/main.py, so web is three levels up
if os.path.exists("/app/web"):
    # Production environment (Docker/Railway)
    WEB_DIR = Path("/app/web").resolve()
else:
    # Development environment
    WEB_DIR = (Path(__file__).resolve().parent.parent.parent / "web").resolve()

logger.info(f"Web directory resolved to: {WEB_DIR}")
logger.info(f"Web directory exists: {WEB_DIR.exists()}")
if WEB_DIR.exists():
    web_files = list(WEB_DIR.glob("*.html"))
    logger.info(f"Found HTML files in web dir: {[f.name for f in web_files]}")
else:
    logger.warning(f"WEB_DIR does not exist at expected path: {WEB_DIR}")
    # Try alternative paths
    alt_paths = [
        Path("/app/web"),
        Path(__file__).parent.parent / "web", 
        Path(__file__).parent / "web"
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            logger.info(f"Alternative web directory found: {alt_path}")
            WEB_DIR = alt_path
            break

def _read_web_file(filename: str) -> Optional[str]:
    """Read HTML file from web directory with debug logging"""
    file_path = WEB_DIR / filename
    logger.info(f"Attempting to read file: {file_path}")
    logger.info(f"File exists: {file_path.exists()}")
    logger.info(f"File is file: {file_path.is_file()}")
    logger.info(f"WEB_DIR contents: {list(WEB_DIR.iterdir()) if WEB_DIR.exists() else 'WEB_DIR does not exist'}")
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()
            logger.info(f"Successfully read {filename}, content length: {len(content)}")
            return content
    except FileNotFoundError:
        logger.error(f"Web file not found: {file_path}")
        logger.error(f"Current working directory: {Path.cwd()}")
        logger.error(f"__file__ location: {Path(__file__).resolve()}")
        return None
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return None

# Debug route to test backend connectivity
@app.get("/api/test", include_in_schema=False)
async def test_api():
    """Simple test endpoint to verify backend is working"""
    return {
        "status": "ok", 
        "message": "Backend is accessible",
        "web_dir": str(WEB_DIR),
        "web_dir_exists": WEB_DIR.exists(),
        "cwd": str(Path.cwd()),
        "file_location": str(Path(__file__).resolve())
    }

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

@app.get("/subscribe", response_class=HTMLResponse, include_in_schema=False)
async def subscribe_page(request: Request):  # noqa: D401
    """Serve simplified single-plan subscription page (subscribe.html)."""
    content = _read_web_file("subscribe.html")
    if content is None:
        # Fallback helpful message if file missing or not deployed
        return HTMLResponse(
            content=(
                "<h1>Subscription Page Not Deployed</h1>"
                "<p>The file subscribe.html was not found in the web directory.</p>"
                "<p>Ensure web/subscribe.html exists in the deployment artifact.</p>"
            ),
            status_code=404
        )
    return HTMLResponse(content=content)

@app.get("/pricing", include_in_schema=False)
async def pricing_redirect():  # noqa: D401
    return Response(status_code=307, headers={"Location": "/subscribe"})

@app.get("/trial-signup", include_in_schema=False)
async def trial_signup_redirect():  # noqa: D401
    return Response(status_code=307, headers={"Location": "/subscribe"})

@app.get("/trial-signup-stripe", include_in_schema=False)
async def trial_signup_stripe_redirect():  # noqa: D401
    return Response(status_code=307, headers={"Location": "/subscribe"})

@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():  # noqa: D401
    """Return list of registered route paths (debug)."""
    try:
        route_info = []
        for r in app.router.routes:
            path = getattr(r, 'path', None)
            methods = list(getattr(r, 'methods', [])) if hasattr(r, 'methods') else []
            if path:
                route_info.append({"path": path, "methods": methods})
        route_info.sort(key=lambda x: x["path"])  # stable ordering
        return {"count": len(route_info), "routes": route_info}
    except Exception as e:
        return {"error": str(e)}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():  # noqa: D401
    """Return favicon if present; suppress 404 noise if missing."""
    # Prefer SVG (crisper scaling) even if a placeholder .ico exists
    svg_path = WEB_DIR / "favicon.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    icon_path = WEB_DIR / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    # Return a 1x1 transparent PNG so browsers cache it and stop requesting
    transparent_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\x0b\x0e\x02\xb5\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return Response(content=transparent_png, media_type="image/png", status_code=200)

# Mount static files for web assets and add direct routes for key pages

# Mount /web for static assets (js, images, etc.)
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")
    # Add backup mount for simpler CSS paths (/static/css/tailwind.css)
    static_dir = WEB_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("Static assets available at both /web/static and /static")
    # Also mount /assets if repository has compiled assets (Tailwind build output)
    assets_dir_candidates = [
        Path(project_root) / "assets",
        Path(project_root) / "public" / "assets"
    ]
    for assets_dir in assets_dir_candidates:
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            logger.info(f"✅ Mounted assets directory at /assets from {assets_dir}")
            break
    else:
        logger.warning("⚠️ No assets directory found to mount at /assets (styles.css 404 risk)")
    logger.info(f"Web directory mounted from: {WEB_DIR}")

    # Explicit route for Tailwind CSS (some platforms mis-handle nested static dirs)
    @app.get("/web/static/css/tailwind.css", include_in_schema=False)
    async def tailwind_css():  # noqa: D401
        """Serve compiled Tailwind CSS with light caching and ETag for busting."""
        css_file = WEB_DIR / "static" / "css" / "tailwind.css"
        if css_file.exists():
            headers = {
                "Cache-Control": "public, max-age=300",  # 5 minutes
                "ETag": str(css_file.stat().st_mtime_ns)
            }
            return FileResponse(str(css_file), media_type="text/css", headers=headers)
        return Response(status_code=404, content="/* tailwind.css missing */", media_type="text/css")

    # Provide legacy/alternate path commonly expected (/static/css/tailwind.css)
    @app.get("/static/css/tailwind.css", include_in_schema=False)
    async def tailwind_css_alias():  # noqa: D401
        css_file = WEB_DIR / "static" / "css" / "tailwind.css"
        if css_file.exists():
            headers = {
                "Cache-Control": "public, max-age=300",
                "ETag": str(css_file.stat().st_mtime_ns)
            }
            return FileResponse(str(css_file), media_type="text/css", headers=headers)
        return Response(status_code=404, content="/* tailwind.css missing (alias) */", media_type="text/css")

    @app.get("/login", response_class=FileResponse, include_in_schema=False)
    async def login_page():  # noqa: D401
        return FileResponse(str(WEB_DIR / "login.html"))

    @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard_page(request: Request):  # noqa: D401
        """Smart dashboard route - checks authentication and redirects appropriately."""
        
        # Check for successful checkout parameters
        plan = request.query_params.get("plan")
        success = request.query_params.get("success")
        
        # If coming from successful checkout, show welcome page and guide to login/signup
        if success == "true" and plan:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html><head><title>Payment Successful - Welcome to A³E Platform</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #fff;
                }}
                .success-container {{
                    text-align: center;
                    padding: 3rem 2rem;
                    max-width: 500px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .success-icon {{
                    width: 80px;
                    height: 80px;
                    background: #10b981;
                    border-radius: 50%;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 2rem;
                    font-size: 2.5rem;
                }}
                h1 {{ margin-bottom: 1rem; font-size: 2rem; }}
                p {{ margin-bottom: 1.5rem; font-size: 1.1rem; opacity: 0.9; }}
                .plan-info {{ 
                    background: rgba(255, 255, 255, 0.1); 
                    padding: 1rem; 
                    border-radius: 10px; 
                    margin: 2rem 0;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .cta-buttons {{ margin-top: 2rem; }}
                .btn {{
                    display: inline-block;
                    padding: 0.875rem 2rem;
                    margin: 0.5rem;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                }}
                .btn-primary {{
                    background: #10b981;
                    color: white;
                }}
                .btn-primary:hover {{
                    background: #059669;
                    transform: translateY(-2px);
                }}
                .btn-secondary {{
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }}
                .btn-secondary:hover {{
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                }}
            </style>
            </head>
            <body>
                <div class="success-container">
                    <div class="success-icon">🎉</div>
                    <h1>Payment Successful!</h1>
                    <p>Welcome to A³E MapMyStandards Platform</p>
                    
                    <div class="plan-info">
                        <strong>Your {plan.title()} Plan is Active</strong>
                        <br>You now have full access to our platform features
                    </div>
                    
                    <p>To access your personalized dashboard and start using the platform:</p>
                    
                    <div class="cta-buttons">
                        <a href="/trial-signup" class="btn btn-primary">Create Your Account →</a>
                        <a href="/login" class="btn btn-secondary">Sign In</a>
                    </div>
                    
                    <p style="font-size: 0.9rem; margin-top: 2rem; opacity: 0.7;">
                        Need help? <a href="/contact" style="color: #10b981;">Contact Support</a>
                    </p>
                </div>
                
                <script>
                    // Store plan info for account creation
                    localStorage.setItem('a3e_subscription_plan', '{plan}');
                    localStorage.setItem('a3e_subscription_active', 'true');
                    localStorage.setItem('a3e_payment_success', Date.now().toString());
                </script>
            </body></html>
            """)
        
        # Check if user is authenticated (check for session token/cookie)
        auth_token = request.cookies.get("auth_token") or request.headers.get("Authorization")
        trial_id = request.cookies.get("a3e_trial_id") or request.headers.get("X-Trial-ID")
        
        # If user has authentication, serve the actual dashboard
        if auth_token or trial_id:
            # Try to serve dashboard-fixed.html (the actual dashboard) first
            dashboard_fixed_file = WEB_DIR / "dashboard-fixed.html"
            if dashboard_fixed_file.exists():
                return FileResponse(str(dashboard_fixed_file))
            
            # Fallback to regular dashboard
            dashboard_file = WEB_DIR / "dashboard-page.html"
            if dashboard_file.exists():
                return FileResponse(str(dashboard_file))
        
        # If no authentication, redirect to login page
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><title>A³E Platform - Authentication Required</title>
        <meta http-equiv="refresh" content="2; url=/login"></head>
        <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem; background: #f8fafc;">
            <div style="width: 60px; height: 60px; background: #3b82f6; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 2rem;">
                <span style="color: white; font-size: 1.5rem;">🔐</span>
            </div>
            <h1 style="color: #1e293b; margin-bottom: 1rem;">Authentication Required</h1>
            <p style="color: #64748b; margin-bottom: 2rem;">Please sign in to access your A³E dashboard.</p>
            <p><a href="/login" style="display: inline-block; background: #1e40af; color: white; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600;">Sign In →</a></p>
        </body></html>
        """)

    @app.get("/dashboard.html", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard_html_page():  # noqa: D401
        """Redirect dashboard.html to /dashboard for compatibility."""
        # Redirect to the proper dashboard route
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><title>Redirecting...</title>
        <meta http-equiv="refresh" content="0; url=/dashboard"></head>
        <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem;">
            <p>Redirecting to dashboard...</p>
            <script>window.location.href = '/dashboard';</script>
        </body></html>
        """)

    @app.get("/homepage", response_class=FileResponse, include_in_schema=False)
    async def homepage():  # noqa: D401
        return FileResponse(str(WEB_DIR / "homepage.html"))

    @app.get("/trial-signup.html", response_class=HTMLResponse, include_in_schema=False)
    async def trial_signup_html():  # noqa: D401
        """Serve trial-signup.html - required for redirect compatibility."""
        signup_file = WEB_DIR / "trial-signup.html"
        if signup_file.exists():
            return FileResponse(str(signup_file))
        # Redirect to non-.html version
        return HTMLResponse("<html><head><meta http-equiv='refresh' content='0; url=/trial-signup'></head><body>Redirecting...</body></html>")

    @app.get("/stripe-checkout-redirect.html", response_class=HTMLResponse, include_in_schema=False)
    async def stripe_checkout_redirect_html():  # noqa: D401
        """Serve stripe-checkout-redirect.html - required for professional checkout flow."""
        checkout_file = WEB_DIR / "stripe-checkout-redirect.html"
        if checkout_file.exists():
            return FileResponse(str(checkout_file))
        # Fallback redirect to homepage
        return HTMLResponse("<html><head><meta http-equiv='refresh' content='0; url=/'></head><body>Redirecting to homepage...</body></html>")
    
    @app.get("/trial-success.html", response_class=HTMLResponse, include_in_schema=False)
    async def trial_success_html():  # noqa: D401
        """Serve trial-success.html - required for redirect compatibility."""
        success_file = WEB_DIR / "trial-success.html"
        if success_file.exists():
            return FileResponse(str(success_file))
        # Fallback success page
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><title>Welcome to A³E Platform!</title></head>
        <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem; background: #f8fafc;">
            <div style="width: 80px; height: 80px; background: #10b981; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 2rem;">
                <span style="color: white; font-size: 2.5rem; font-weight: bold;">✓</span>
            </div>
            <h1 style="color: #1e293b; margin-bottom: 1rem;">Welcome to A³E Platform!</h1>
            <p style="color: #64748b; margin-bottom: 2rem;">Your account is ready and the platform is operational.</p>
            <div style="background: white; border-radius: 12px; padding: 2rem; max-width: 500px; margin: 2rem auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-bottom: 1rem; color: #1e293b;">What's Next:</h3>
                <ul style="text-align: left; color: #475569; line-height: 1.6;">
                    <li>✅ Your trial account is active</li>
                    <li>🔧 Platform features are being updated</li>
                    <li>📧 Check your email for account details</li>
                    <li>💬 Contact support for immediate assistance</li>
                </ul>
            </div>
            <div style="margin-top: 2rem;">
                <a href="mailto:support@mapmystandards.ai" style="display: inline-block; background: #1e40af; color: white; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; margin-right: 1rem;">📧 Contact Support</a>
                <a href="/dashboard" style="display: inline-block; background: #64748b; color: white; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600;">🏠 Go to Dashboard</a>
            </div>
        </body></html>
        """)
    
    @app.get("/quick-wins-dashboard", response_class=FileResponse, include_in_schema=False)
    async def quick_wins_dashboard():  # noqa: D401
        """Serve quick wins dashboard for trial users."""
        return FileResponse(str(WEB_DIR / "quick-wins-dashboard.html"))
    
    @app.get("/roi-calculator", response_class=FileResponse, include_in_schema=False)
    async def roi_calculator():  # noqa: D401
        """Serve ROI calculator tool."""
        return FileResponse(str(WEB_DIR / "roi-calculator.html"))

    @app.get("/onboarding", response_class=FileResponse, include_in_schema=False)
    @app.get("/onboarding.html", response_class=FileResponse, include_in_schema=False)
    async def onboarding_page():  # noqa: D401
        """Serve onboarding wizard page."""
        target = WEB_DIR / "onboarding.html"
        if target.exists():
            return FileResponse(str(target))
        return HTMLResponse("<h1>Onboarding page not found</h1>", status_code=404)
    
    @app.get("/standards", response_class=FileResponse, include_in_schema=False)
    async def standards_page():  # noqa: D401
        """Serve standards page."""
        return FileResponse(str(WEB_DIR / "standards.html"))
    
    @app.get("/reports", response_class=FileResponse, include_in_schema=False)
    async def reports_page():  # noqa: D401
        """Serve reports page."""
        return FileResponse(str(WEB_DIR / "reports.html"))
    
    @app.get("/upload", response_class=FileResponse, include_in_schema=False)
    async def upload_page():  # noqa: D401
        """Serve upload page."""
        return FileResponse(str(WEB_DIR / "upload.html"))
        
else:
    logger.warning(f"Web directory not found at: {WEB_DIR}")
    # Try alternative path for Railway deployment
    alt_web_directory = "web"
    if os.path.exists(alt_web_directory):
        app.mount("/web", StaticFiles(directory=alt_web_directory), name="web")
        logger.info(f"Web directory mounted from alternative path: {alt_web_directory}")

        # Add direct routes for key pages
        @app.get("/login", response_class=FileResponse, include_in_schema=False)
        async def login_page():  # noqa: D401
            return FileResponse(os.path.join(alt_web_directory, "login.html"))

        @app.get("/checkout", response_class=FileResponse, include_in_schema=False)
        async def checkout_page_alt():  # noqa: D401 - alt name to avoid redefinition
            return FileResponse(os.path.join(alt_web_directory, "checkout.html"))

        @app.get("/homepage", response_class=FileResponse, include_in_schema=False)
        async def homepage():  # noqa: D401
            return FileResponse(os.path.join(alt_web_directory, "homepage.html"))

        @app.get("/onboarding", response_class=FileResponse, include_in_schema=False)
        @app.get("/onboarding.html", response_class=FileResponse, include_in_schema=False)
        async def onboarding_page():  # noqa: D401
            target = os.path.join(alt_web_directory, "onboarding.html")
            if os.path.exists(target):
                return FileResponse(target)
            return HTMLResponse("<h1>Onboarding page not found</h1>", status_code=404)
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
