"""API endpoints for sample data and guided tutorials."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ...core.config import settings
from ...services.sample_data_service import SampleDataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sample-data", tags=["sample-data"])

class TutorialRequest(BaseModel):
    user_goals: List[str]
    institution_profile: Dict[str, Any]
    email: Optional[str] = None

class DemoAccountRequest(BaseModel):
    user_email: str
    institution_profile: Dict[str, Any]
    onboarding_data: Optional[Dict[str, Any]] = None

@router.get("/quick-wins")
async def get_quick_wins(
    goals: Optional[str] = Query(None, description="Comma-separated user goals"),
    institution_size: Optional[str] = Query("5k_15k", description="Institution size category")
):
    """Get personalized quick wins based on user goals."""
    try:
        sample_service = SampleDataService()
        user_goals = goals.split(',') if goals else ['Map standards quickly', 'Track progress']
        
        # Generate contextual quick wins
        sample_institution = sample_service.get_sample_institution(enrollment_range=institution_size)
        tutorial_data = sample_service.generate_tutorial_data(user_goals, sample_institution)
        
        return {
            "success": True,
            "quick_wins": tutorial_data["quick_wins"],
            "institution_context": tutorial_data["institution_context"],
            "guided_steps": tutorial_data["guided_steps"]
        }
    except Exception as e:
        logger.error(f"Failed to generate quick wins: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quick wins")

@router.get("/roi-calculator")
async def get_roi_calculator(
    size: str = Query("5k_15k", description="Institution size for ROI calculation")
):
    """Get ROI calculator data customized for institution size."""
    try:
        sample_service = SampleDataService()
        roi_data = sample_service.get_roi_calculator_data(size)
        
        return {
            "success": True,
            "roi_data": roi_data,
            "size_category": size
        }
    except Exception as e:
        logger.error(f"Failed to calculate ROI: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate ROI")

@router.post("/tutorial")
async def generate_tutorial(request: TutorialRequest):
    """Generate personalized tutorial based on user goals and profile."""
    try:
        sample_service = SampleDataService()
        tutorial_data = sample_service.generate_tutorial_data(
            request.user_goals, 
            request.institution_profile
        )
        
        return {
            "success": True,
            "tutorial_data": tutorial_data,
            "estimated_duration": f"{len(tutorial_data['guided_steps']) * 2} minutes"
        }
    except Exception as e:
        logger.error(f"Failed to generate tutorial: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate tutorial")

@router.post("/demo-account")
async def create_demo_account(request: DemoAccountRequest):
    """Create comprehensive demo data for a trial account."""
    try:
        sample_service = SampleDataService()
        demo_data = sample_service.create_demo_account_data(
            request.user_email,
            request.institution_profile
        )
        
        # Store demo data in user session/profile
        # This would typically integrate with your user management system
        
        return {
            "success": True,
            "demo_data": demo_data,
            "message": "Demo account created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create demo account: {e}")
        raise HTTPException(status_code=500, detail="Failed to create demo account")

@router.get("/welcome-dashboard")
async def get_welcome_dashboard(
    goals: Optional[str] = Query(None, description="Comma-separated user goals"),
    institution_name: Optional[str] = Query(None),
    institution_size: Optional[str] = Query("5k_15k"),
    primary_accreditor: Optional[str] = Query(None)
):
    """Get personalized welcome dashboard data."""
    try:
        sample_service = SampleDataService()
        
        user_goals = goals.split(',') if goals else ['Map standards quickly']
        institution_data = {
            "institution_name": institution_name,
            "institution_size": institution_size,
            "primary_accreditor": primary_accreditor
        }
        
        dashboard_data = sample_service.generate_welcome_dashboard_data(
            user_goals, 
            institution_data
        )
        
        return {
            "success": True,
            "dashboard_data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Failed to generate welcome dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard data")

@router.get("/sample-institutions")
async def get_sample_institutions():
    """Get list of sample institutions for reference."""
    try:
        sample_service = SampleDataService()
        return {
            "success": True,
            "institutions": sample_service.SAMPLE_INSTITUTIONS,
            "count": len(sample_service.SAMPLE_INSTITUTIONS)
        }
    except Exception as e:
        logger.error(f"Failed to get sample institutions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample institutions")

@router.get("/sample-documents")
async def get_sample_documents(
    goals: Optional[str] = Query(None, description="Comma-separated user goals"),
    institution_type: Optional[str] = Query(None)
):
    """Get relevant sample documents based on user goals."""
    try:
        sample_service = SampleDataService()
        user_goals = goals.split(',') if goals else ['Map standards quickly']
        
        sample_institution = sample_service.get_sample_institution(institution_type)
        documents = sample_service._generate_sample_documents(user_goals, sample_institution)
        
        return {
            "success": True,
            "documents": documents,
            "institution_context": sample_institution["name"]
        }
    except Exception as e:
        logger.error(f"Failed to get sample documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample documents")

@router.get("/success-metrics/{institution_size}")
async def get_success_metrics(institution_size: str):
    """Get success metrics for similar institutions."""
    try:
        sample_service = SampleDataService()
        sample_institution = sample_service.get_sample_institution(enrollment_range=institution_size)
        
        return {
            "success": True,
            "metrics": sample_institution["success_metrics"],
            "institution_profile": {
                "name": sample_institution["name"],
                "type": sample_institution["type"],
                "enrollment": sample_institution["enrollment"],
                "accreditor": sample_institution["accreditor"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get success metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get success metrics")

@router.post("/track-tutorial-progress")
async def track_tutorial_progress(
    step_id: str,
    completed: bool = True,
    user_email: Optional[str] = None
):
    """Track user progress through tutorial steps."""
    try:
        # This would integrate with your analytics/user tracking system
        progress_data = {
            "user_email": user_email,
            "step_id": step_id,
            "completed": completed,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Tutorial progress tracked: {progress_data}")
        
        return {
            "success": True,
            "message": "Progress tracked successfully"
        }
    except Exception as e:
        logger.error(f"Failed to track tutorial progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to track progress")

@router.get("/onboarding-insights")
async def get_onboarding_insights(
    email: Optional[str] = Query(None)
):
    """Get insights and tips based on onboarding data."""
    try:
        # This could analyze user's onboarding choices and provide personalized insights
        insights = {
            "personalized_tips": [
                "Based on your goals, focus on standards mapping first",
                "Your institution size suggests prioritizing efficiency features",
                "Consider starting with your strategic planning documents"
            ],
            "recommended_next_steps": [
                "Upload your first strategic document",
                "Review the AI mapping results",
                "Generate your first compliance report"
            ],
            "estimated_time_to_value": "15 minutes",
            "similar_institutions_success": "94% of similar institutions see value within first week"
        }
        
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Failed to get onboarding insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")