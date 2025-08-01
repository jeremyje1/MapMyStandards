"""
Contact form handler for MapMyStandards.ai
API endpoint for processing contact form submissions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contact", tags=["contact"])

class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str
    phone: Optional[str] = None
    organization: Optional[str] = None

class ContactFormResponse(BaseModel):
    success: bool
    message: str

@router.post("/submit", response_model=ContactFormResponse)
async def submit_contact_form(request: ContactFormRequest):
    """
    Handle contact form submission from website
    """
    try:
        # Validate input
        if not request.name.strip() or not request.message.strip():
            raise HTTPException(
                status_code=400, 
                detail="Name and message are required"
            )
        
        # Send email notification
        success = email_service.send_contact_form_email(
            name=request.name,
            email=str(request.email),
            message=request.message
        )
        
        if success:
            logger.info(f"Contact form submitted by {request.name} ({request.email})")
            return ContactFormResponse(
                success=True,
                message="Thank you for your message. We'll get back to you soon!"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email. Please try again later."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing contact form: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )

@router.post("/demo-request", response_model=ContactFormResponse)
async def request_demo(request: ContactFormRequest):
    """
    Handle demo request submissions
    """
    try:
        # Enhanced email for demo requests
        subject = f"Demo Request from {request.name} - {request.organization or 'Organization'}"
        
        message_body = f"""
DEMO REQUEST RECEIVED

Contact Information:
- Name: {request.name}
- Email: {request.email}
- Organization: {request.organization or 'Not specified'}
- Phone: {request.phone or 'Not provided'}

Message:
{request.message}

---
Priority: HIGH - Demo Request
Sent from MapMyStandards.ai demo request form
        """
        
        # Send to support team
        success = email_service.send_email(
            to_emails=['support@mapmystandards.ai'],
            subject=subject,
            body=message_body,
            from_email='support@mapmystandards.ai'
        )
        
        if success:
            logger.info(f"Demo request submitted by {request.name} ({request.email})")
            return ContactFormResponse(
                success=True,
                message="Thank you for your demo request. Our team will contact you within 24 hours!"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send demo request. Please try again later."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing demo request: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )
