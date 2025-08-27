"""API endpoints for email nurturing sequences."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ...core.config import settings
from ...services.email_nurturing_service import EmailNurturingService, NurturingStage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nurturing", tags=["nurturing"])

class NurturingSetupRequest(BaseModel):
    user_email: EmailStr
    user_data: Dict[str, Any]
    onboarding_data: Optional[Dict[str, Any]] = None

class EmailEngagementRequest(BaseModel):
    user_email: EmailStr
    email_stage: str
    action: str  # opened, clicked, converted, unsubscribed

class NurturingPreferencesRequest(BaseModel):
    user_email: EmailStr
    frequency: str = "standard"  # standard, minimal, off
    interests: List[str] = []

@router.post("/setup")
async def setup_nurturing_sequence(
    request: NurturingSetupRequest,
    background_tasks: BackgroundTasks
):
    """Set up automated email nurturing sequence for a new trial user."""
    try:
        nurturing_service = EmailNurturingService()
        
        # Generate personalized nurturing schedule
        schedule = nurturing_service.get_nurturing_schedule(request.user_data)
        
        # In a real implementation, you would:
        # 1. Store the schedule in your database
        # 2. Set up scheduled tasks (e.g., Celery, AWS Lambda, etc.)
        # 3. Configure your email service (Postmark, SendGrid, etc.)
        
        # For now, log the schedule
        logger.info(f"Nurturing sequence created for {request.user_email}: {len(schedule)} emails scheduled")
        
        # Schedule the first email as background task
        background_tasks.add_task(
            schedule_first_email,
            request.user_email,
            schedule[0] if schedule else None
        )
        
        return {
            "success": True,
            "sequence_created": True,
            "emails_scheduled": len(schedule),
            "first_email_stage": schedule[0]["stage"] if schedule else None,
            "estimated_send_times": [
                {
                    "stage": email["stage"],
                    "send_time": email["send_time"].isoformat()
                }
                for email in schedule
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to setup nurturing sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup nurturing sequence")

@router.get("/preview/{stage}")
async def preview_email(
    stage: str,
    user_email: Optional[str] = None,
    institution_name: Optional[str] = None,
    institution_size: Optional[str] = None,
    primary_accreditor: Optional[str] = None
):
    """Preview an email from the nurturing sequence."""
    try:
        nurturing_service = EmailNurturingService()
        
        # Create sample user data for preview
        sample_user_data = {
            "user_email": user_email or "preview@example.com",
            "institution_name": institution_name or "Sample University",
            "institution_size": institution_size or "5k_15k",
            "primary_accreditor": primary_accreditor or "HLC",
            "signup_date": datetime.utcnow(),
            "goals": ["Map standards quickly", "Track progress"],
            "documents_analyzed": 3,
            "tutorial_completed": False
        }
        
        # Get email configuration for the stage
        if stage not in nurturing_service.email_sequences:
            raise HTTPException(status_code=404, detail="Email stage not found")
        
        email_config = nurturing_service.email_sequences[stage]
        personalized_content = nurturing_service._personalize_content(email_config, sample_user_data)
        
        # Generate HTML preview
        html_content = nurturing_service.generate_email_html(personalized_content)
        
        return {
            "success": True,
            "stage": stage,
            "subject": personalized_content["subject"],
            "html_content": html_content,
            "content_blocks": personalized_content.get("content_blocks", []),
            "personalization_data": sample_user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview email: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview email")

@router.post("/track-engagement")
async def track_email_engagement(request: EmailEngagementRequest):
    """Track email engagement for analytics and optimization."""
    try:
        nurturing_service = EmailNurturingService()
        
        engagement_data = nurturing_service.track_email_engagement(
            request.user_email,
            request.email_stage,
            request.action
        )
        
        # Update user's nurturing sequence based on engagement
        if request.action == "converted":
            await pause_nurturing_sequence(request.user_email, "converted")
        elif request.action == "unsubscribed":
            await pause_nurturing_sequence(request.user_email, "unsubscribed")
        
        return {
            "success": True,
            "engagement_tracked": True,
            "action": request.action,
            "timestamp": engagement_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Failed to track engagement: {e}")
        raise HTTPException(status_code=500, detail="Failed to track engagement")

@router.put("/preferences")
async def update_nurturing_preferences(request: NurturingPreferencesRequest):
    """Update user's email nurturing preferences."""
    try:
        # In a real implementation, you would:
        # 1. Update user preferences in database
        # 2. Modify scheduled email sequences
        # 3. Update email frequency and content focus
        
        logger.info(f"Nurturing preferences updated for {request.user_email}: {request.frequency}")
        
        return {
            "success": True,
            "preferences_updated": True,
            "frequency": request.frequency,
            "interests": request.interests
        }
        
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

@router.get("/performance")
async def get_sequence_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get performance metrics for email nurturing sequences."""
    try:
        nurturing_service = EmailNurturingService()
        
        # Parse date range if provided
        date_range = None
        if start_date and end_date:
            date_range = {
                "start": datetime.fromisoformat(start_date),
                "end": datetime.fromisoformat(end_date)
            }
        
        performance_data = nurturing_service.get_sequence_performance(date_range)
        
        return {
            "success": True,
            "performance_data": performance_data,
            "date_range": date_range
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance data")

@router.get("/stages")
async def get_nurturing_stages():
    """Get all available nurturing stages and their descriptions."""
    try:
        stage_info = {
            NurturingStage.WELCOME.value: {
                "name": "Welcome",
                "description": "Initial welcome and onboarding guidance",
                "timing": "1 hour after signup"
            },
            NurturingStage.VALUE_DEMO.value: {
                "name": "Value Demonstration",
                "description": "Show ROI and time savings with social proof",
                "timing": "Day 2"
            },
            NurturingStage.FEATURE_INTRO.value: {
                "name": "Feature Introduction",
                "description": "Deep dive into advanced platform features",
                "timing": "Day 4"
            },
            NurturingStage.SUCCESS_STORIES.value: {
                "name": "Success Stories",
                "description": "Case studies and peer institution results",
                "timing": "Day 6"
            },
            NurturingStage.ROI_FOCUS.value: {
                "name": "ROI Focus",
                "description": "Personalized ROI calculation and cost comparison",
                "timing": "Day 8"
            },
            NurturingStage.URGENCY_CONVERSION.value: {
                "name": "Urgency Conversion",
                "description": "Trial ending reminder with progress summary",
                "timing": "Day 11"
            },
            NurturingStage.LAST_CHANCE.value: {
                "name": "Last Chance",
                "description": "Final conversion opportunity",
                "timing": "Day 14"
            }
        }
        
        return {
            "success": True,
            "stages": stage_info,
            "total_stages": len(stage_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to get nurturing stages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stages")

@router.post("/pause/{user_email}")
async def pause_nurturing_sequence(user_email: str, reason: str = "user_request"):
    """Pause nurturing sequence for a user."""
    try:
        # In a real implementation, you would:
        # 1. Mark the sequence as paused in database
        # 2. Cancel scheduled email tasks
        # 3. Log the reason for pausing
        
        logger.info(f"Nurturing sequence paused for {user_email}, reason: {reason}")
        
        return {
            "success": True,
            "sequence_paused": True,
            "reason": reason,
            "paused_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to pause sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause sequence")

@router.post("/resume/{user_email}")
async def resume_nurturing_sequence(user_email: str):
    """Resume paused nurturing sequence for a user."""
    try:
        # In a real implementation, you would:
        # 1. Update sequence status in database
        # 2. Reschedule remaining emails
        # 3. Adjust timing based on pause duration
        
        logger.info(f"Nurturing sequence resumed for {user_email}")
        
        return {
            "success": True,
            "sequence_resumed": True,
            "resumed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to resume sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume sequence")

# Background task functions
async def schedule_first_email(user_email: str, email_data: Optional[Dict[str, Any]]):
    """Background task to schedule the first nurturing email."""
    if not email_data:
        return
    
    logger.info(f"First nurturing email scheduled for {user_email}: {email_data['stage']}")
    
    # In a real implementation, this would:
    # 1. Queue the email with your email service
    # 2. Set up the schedule for future emails
    # 3. Update user's nurturing status
    
    return {"scheduled": True}