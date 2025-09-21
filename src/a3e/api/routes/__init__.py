"""
API Routes initialization for A3E

Aggregates and configures all API route modules.
"""

from fastapi import APIRouter
from .institutions import router as institutions_router
from .standards import router as standards_router
from .evidence import router as evidence_router
from .workflows import router as workflows_router
from .integrations import router as integrations_router
from .proprietary import router as proprietary_router
from .auth import router as auth_router
from .onboarding import router as onboarding_router
from .sample_data import router as sample_data_router
from .nurturing import router as nurturing_router
from .org_chart import router as org_chart_router
from .scenarios import router as scenarios_router
from .enterprise_metrics import router as enterprise_metrics_router
from .powerbi import router as powerbi_router
from .teams import router as teams_router
from .audit_logs import router as audit_logs_router
from .sso import router as sso_router
from .webhooks import router as webhooks_router

# Create main API router
api_router = APIRouter()

# Include all route modules with prefixes
api_router.include_router(
    institutions_router,
    prefix="/institutions",
    tags=["institutions"]
)

api_router.include_router(
    standards_router,
    prefix="/standards",
    tags=["standards"]
)

api_router.include_router(
    evidence_router,
    prefix="/evidence",
    tags=["evidence"]
)

api_router.include_router(
    workflows_router,
    prefix="/workflows",
    tags=["workflows"]
)

api_router.include_router(
    integrations_router,
    tags=["integrations"]
)

# Include new customer experience routes
api_router.include_router(onboarding_router)
api_router.include_router(sample_data_router)  
api_router.include_router(nurturing_router)

# Include new feature routes
api_router.include_router(org_chart_router, tags=["organization"])
api_router.include_router(scenarios_router, tags=["scenarios"])
api_router.include_router(enterprise_metrics_router, tags=["metrics"])
api_router.include_router(powerbi_router, tags=["powerbi"])

# Include enterprise features
api_router.include_router(teams_router, prefix="/teams", tags=["teams"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit"])
api_router.include_router(sso_router, prefix="/sso", tags=["sso"])

# Include webhook management
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

# Configuration router not yet implemented

__all__ = ["api_router"]
