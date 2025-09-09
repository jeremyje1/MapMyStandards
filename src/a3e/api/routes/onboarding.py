"""Onboarding progress endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...models.user import User
from ...services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

class OnboardingProgress(BaseModel):
    data: Dict[str, Any]
    step: int
    complete: bool = False
    email: Optional[str] = None

async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

@router.post("/progress")
async def save_progress(payload: OnboardingProgress, db: AsyncSession = Depends(get_db)):
    try:
        # Identify user by email if provided; otherwise ignore persistence
        if not payload.email and 'email' in payload.data:
            payload.email = payload.data.get('email')
        if not payload.email:
            return {"saved": False}
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if not user:
            return {"saved": False}
        # Merge onboarding data (preserve prior answers and update current step fields)
        existing = user.onboarding_data or {}
        # Store step-wise responses under keys; also maintain a flat merged dict for convenience
        existing_steps = existing.get('steps', {})
        existing_steps[f'step_{payload.step}'] = payload.data
        # Build merged flat view
        merged_flat = existing.get('merged', {})
        merged_flat.update(payload.data)
        existing['steps'] = existing_steps
        existing['merged'] = merged_flat
        existing['last_step'] = payload.step
        existing['updated_at'] = datetime.utcnow().isoformat()
        if payload.complete:
            existing['completed_at'] = datetime.utcnow().isoformat()
            user.onboarding_completed = True
        user.onboarding_data = existing

        # Map a few strategic fields onto first-class columns if empty
        changed = False
        if 'institution_name' in payload.data and not getattr(user, 'institution_name', None):
            try:
                user.institution_name = payload.data['institution_name']  # type: ignore[attr-defined]
                changed = True
            except Exception:
                pass
        if 'primary_accreditor' in payload.data and not user.role:
            user.role = payload.data['primary_accreditor']
            changed = True
        if payload.complete and not user.is_verified:
            user.is_verified = True
            changed = True
        if changed:
            user.updated_at = datetime.utcnow()
        await db.commit()
        return {"saved": True, "complete": payload.complete, "onboarding_completed": user.onboarding_completed}
    except Exception as e:
        logger.warning(f"Onboarding save failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save progress")


@router.get("/progress/{email}")
async def get_progress(email: str, db: AsyncSession = Depends(get_db)):
    """Return stored onboarding data for a user (if any)."""
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not getattr(user, 'onboarding_data', None):
            return {"found": False}
        return {
            "found": True,
            "completed": bool(getattr(user, 'onboarding_completed', False)),
            "data": user.onboarding_data
        }
    except Exception as e:
        logger.warning(f"Onboarding fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load progress")
