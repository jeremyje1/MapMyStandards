"""
CORS test endpoint for debugging
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["cors-test"])

@router.get("/cors-test")
async def cors_test():
    """Simple endpoint to test CORS headers"""
    return {"status": "ok", "message": "CORS test successful"}

@router.options("/cors-test")
async def cors_test_options():
    """Handle preflight for CORS test"""
    return {"status": "ok"}

@router.options("/auth/login")
async def auth_login_options():
    """Handle preflight for auth login"""
    return {"status": "ok"}