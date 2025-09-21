"""
User Profile Update Endpoint
This ensures onboarding data is saved to the database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ...models.user import User
from ...services.database_service import DatabaseService
from ...core.config import get_settings
from .auth import get_current_user

router = APIRouter(prefix="/api/user/profile", tags=["profile"])
settings = get_settings()

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

class ProfileUpdateRequest(BaseModel):
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None
    role: Optional[str] = None
    primary_accreditor: Optional[str] = None
    state: Optional[str] = None
    institution_size: Optional[str] = None

@router.put("/update")
async def update_user_profile(
    updates: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile in database - called after onboarding"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")
        
        # Build update dict with non-None values
        update_values = {}
        if updates.institution_name is not None:
            update_values["institution_name"] = updates.institution_name
        if updates.institution_type is not None:
            update_values["institution_type"] = updates.institution_type
        if updates.role is not None:
            update_values["role"] = updates.role
        
        # Note: primary_accreditor, state, institution_size might need new columns
        # For now, we'll store them in a JSON field if available
        
        if not update_values:
            return {"status": "no_changes"}
        
        # Update user in database
        stmt = update(User).where(User.id == user_id).values(**update_values)
        await db.execute(stmt)
        await db.commit()
        
        return {
            "status": "updated",
            "updated_fields": list(update_values.keys())
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.get("/")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile from database"""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found")
        
        # Get user from database
        from sqlalchemy import select
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "institution_name": user.institution_name,
            "institution_type": user.institution_type,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")