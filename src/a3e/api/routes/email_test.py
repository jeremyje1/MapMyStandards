"""
Email Testing API Routes

Provides endpoints for testing and monitoring email configuration.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from ...services.email_service_postmark import get_email_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email", tags=["email"])

@router.get("/test")
async def test_email_configuration(
    current_user: dict = Depends(get_current_user)
):
    """Test email configuration and send a test email"""
    
    try:
        email_service = get_email_service()
        result = email_service.test_email_configuration()
        
        return {
            "success": result['test_sent'],
            "data": result,
            "message": "Email test completed" if result['test_sent'] else "Email test failed"
        }
    except Exception as e:
        logger.error(f"Email test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-welcome")
async def send_welcome_email(
    email: str,
    name: str = "User",
    current_user: dict = Depends(get_current_user)
):
    """Send a welcome email (for testing)"""
    
    try:
        email_service = get_email_service()
        success = email_service.send_trial_welcome(email, name)
        
        return {
            "success": success,
            "message": f"Welcome email {'sent' if success else 'failed'} to {email}"
        }
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-document-notification")
async def send_document_notification(
    email: str,
    document_name: str = "Sample Document.pdf",
    standards_mapped: int = 15,
    confidence_score: float = 92.5,
    current_user: dict = Depends(get_current_user)
):
    """Send a document processed notification (for testing)"""
    
    try:
        email_service = get_email_service()
        success = email_service.send_document_processed(
            email, document_name, standards_mapped, confidence_score
        )
        
        return {
            "success": success,
            "message": f"Document notification {'sent' if success else 'failed'} to {email}"
        }
    except Exception as e:
        logger.error(f"Failed to send document notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def email_service_status():
    """Get email service status (no auth required for health check)"""
    
    try:
        email_service = get_email_service()
        
        return {
            "success": True,
            "data": {
                "provider": email_service.provider,
                "configured": email_service.provider is not None,
                "from_email": email_service.from_email,
                "from_name": email_service.from_name
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "provider": None,
                "configured": False,
                "error": str(e)
            }
        }