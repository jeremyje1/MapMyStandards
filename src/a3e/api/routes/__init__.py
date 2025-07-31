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
from .proprietary import router as proprietary_router, config_router

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

api_router.include_router(
    config_router,
    tags=["configuration"]
)

__all__ = ["api_router"]
