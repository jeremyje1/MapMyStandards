from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.a3e.core.database import get_db
from src.a3e.core.auth import get_current_user
from src.a3e.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "organization": current_user.organization,
        "role": current_user.role,
        "onboarding_completed": current_user.onboarding_completed,
        "primary_accreditor": current_user.primary_accreditor
    }

@router.get("/settings") 
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get user settings"""
    return {
        "organization": current_user.organization,
        "primary_accreditor": current_user.primary_accreditor,
        "role": current_user.role,
        "onboarding_completed": current_user.onboarding_completed
    }

@router.post("/settings")
async def update_user_settings(
    settings: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    if "organization" in settings:
        current_user.organization = settings["organization"]
    if "primary_accreditor" in settings:
        current_user.primary_accreditor = settings["primary_accreditor"]
    if "role" in settings:
        current_user.role = settings["role"]
    
    db.commit()
    return {"message": "Settings updated successfully"}
