"""
Tier management endpoints for subscription persistence
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tier", tags=["tier"])

# In-memory storage for demo (replace with DB in production)
user_tiers: Dict[str, Dict[str, Any]] = {}

class TierSyncRequest(BaseModel):
    email: EmailStr
    tier: str
    source: Optional[str] = None

class TierResponse(BaseModel):
    email: str
    tier: str
    updated_at: str
    source: Optional[str] = None

@router.post("/sync", response_model=TierResponse)
async def sync_user_tier(request: TierSyncRequest):
    """
    Sync user tier information from frontend to backend.
    This endpoint is called after successful Stripe checkout.
    """
    try:
        # Validate tier
        valid_tiers = ["department", "campus", "system", "pilot", "trial", "unknown"]
        if request.tier not in valid_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")
        
        # Store tier information
        user_tiers[request.email] = {
            "tier": request.tier,
            "updated_at": datetime.utcnow().isoformat(),
            "source": request.source or "api"
        }
        
        logger.info(f"Tier synced for {request.email}: {request.tier}")
        
        return TierResponse(
            email=request.email,
            tier=request.tier,
            updated_at=user_tiers[request.email]["updated_at"],
            source=request.source
        )
        
    except Exception as e:
        logger.error(f"Error syncing tier: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync tier")

@router.get("/status/{email}", response_model=TierResponse)
async def get_user_tier(email: str):
    """Get current tier for a user"""
    if email not in user_tiers:
        raise HTTPException(status_code=404, detail="User tier not found")
    
    tier_data = user_tiers[email]
    return TierResponse(
        email=email,
        tier=tier_data["tier"],
        updated_at=tier_data["updated_at"],
        source=tier_data.get("source")
    )

@router.get("/health")
async def tier_health_check():
    """Health check for tier service"""
    return {
        "status": "healthy",
        "service": "tier-management",
        "timestamp": datetime.utcnow().isoformat(),
        "active_users": len(user_tiers)
    }
