"""
Trial signup and management endpoints for A3E platform
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
import uuid
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...services.database_service import DatabaseService
from ...core.config import get_settings

router = APIRouter(prefix="/api/trial", tags=["trial"])
settings = get_settings()

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

class TrialSignupRequest(BaseModel):
    name: str
    institution_name: str
    institution_type: Optional[str] = None
    email: EmailStr
    password: str
    role: str
    plan: str = "college_monthly"
    phone: Optional[str] = None
    newsletter_opt_in: bool = False

class TrialSignupResponse(BaseModel):
    success: bool
    trial_id: str
    expires_at: str
    message: str
    api_key: Optional[str] = None

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"mms_{''.join(secrets.token_urlsafe(32))}"

async def send_welcome_email(email: str, name: str, api_key: str):
    """Send welcome email to new trial user"""
    try:
        from ...services.email_service import email_service
        
        # The existing send_welcome_email method doesn't take api_key
        # We'll need to enhance it or use a custom email for now
        success = email_service.send_welcome_email(email, name)
        
        if success:
            print(f"Welcome email sent to {email}")
        else:
            print(f"Failed to send welcome email to {email}")
            
        # TODO: Update email template to include API key and trial info
        
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

async def notify_admin_new_signup(email: str, name: str, institution: Optional[str]):
    """Send admin notification about new signup."""
    try:
        from ...services.email_service import email_service
        email_service.send_admin_new_signup_notification(email, name, institution, trial=True)
    except Exception as e:
        print(f"Failed to send admin signup notification: {e}")

@router.post("/signup", response_model=TrialSignupResponse)
async def signup_trial(
    request: TrialSignupRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new trial account"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check if user already exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists"
            )

        # Create user account
        api_key = generate_api_key()
        password_hash = hash_password(request.password)

        # Calculate trial expiration (7 days)
        trial_expires = datetime.utcnow() + timedelta(days=7)
        
        # Create new user
        new_user = User(
            email=request.email,
            name=request.name,
            institution_name=request.institution_name,
            institution_type=request.institution_type,
            role=request.role,
            password_hash=password_hash,
            api_key=api_key,
            api_key_created_at=datetime.utcnow(),
            trial_started_at=datetime.utcnow(),
            trial_ends_at=trial_expires,
            is_trial=True,
            subscription_tier="trial"
        )
        
        # TODO: Create Stripe customer
        # stripe_customer = stripe.Customer.create(
        #     email=request.email,
        #     name=request.name,
        #     metadata={
        #         "institution": request.institution_name,
        #         "trial_start": datetime.utcnow().isoformat()
        #     }
        # )
        # new_user.stripe_customer_id = stripe_customer.id
        
        # Save to database
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Send welcome + admin notification emails in background
        background_tasks.add_task(send_welcome_email, request.email, request.name, api_key)
        background_tasks.add_task(notify_admin_new_signup, request.email, request.name, request.institution_name)

        logger.info(f"Trial account created for {request.email}")

        return TrialSignupResponse(
            success=True,
            message="Trial account created successfully",
            trial_id=str(new_user.id),
            api_key=api_key,
            expires_at=trial_expires.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trial account: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create trial account"
        )

@router.get("/status/{email}")
async def get_trial_status(email: EmailStr, db: AsyncSession = Depends(get_db)):
    """Get trial account status"""
    from sqlalchemy import select
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": email,
        "trial_active": user.is_trial_active,
        "days_remaining": user.days_remaining_in_trial,
        "expires_at": user.trial_ends_at,
        "subscription_tier": user.subscription_tier
    }

@router.post("/extend/{email}")
async def extend_trial(email: EmailStr, days: int = 7, db: AsyncSession = Depends(get_db)):
    """Extend trial period"""
    from sqlalchemy import select
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Extend trial
    if not user.trial_ends_at:
        # Initialize original trial to 7 days if missing
        user.trial_ends_at = datetime.utcnow() + timedelta(days=7)
    
    user.trial_ends_at = user.trial_ends_at + timedelta(days=days)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "message": f"Trial extended by {days} days",
        "new_expiration": user.trial_ends_at
    }
