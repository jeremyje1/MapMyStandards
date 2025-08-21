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
        # Stash basic onboarding fields into user freeform areas (reuse existing columns)
        changed = False
        if 'institution_name' in payload.data and not user.institution_name:
            user.institution_name = payload.data['institution_name']
            changed = True
        if 'primary_accreditor' in payload.data and not user.role:
            user.role = payload.data['primary_accreditor']  # TEMP repurpose role field until dedicated columns
            changed = True
        if payload.complete and not user.is_verified:
            user.is_verified = True
            changed = True
        if changed:
            user.updated_at = datetime.utcnow()
        await db.commit()
        return {"saved": True, "complete": payload.complete}
    except Exception as e:
        logger.warning(f"Onboarding save failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save progress")
