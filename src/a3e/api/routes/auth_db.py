"""
Database-backed authentication API routes
This version properly stores users in the database for persistence
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets
import time
from datetime import datetime, timedelta
import jwt
import logging

from ...database.models import User
from ...services.database_service import DatabaseService
from ...services.payment_service import PaymentService
from ...services.email_service import EmailService
from ...core.config import get_settings
from .auth_impl import create_jwt_token

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["authentication"])

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Pydantic models
class UserRegistrationRequest(BaseModel):
    first_name: str
    last_name: str
    institution_name: str
    email: EmailStr
    password: str
    role: str = "user"
    plan: str = "professional_monthly"
    phone: Optional[str] = ""
    newsletter_opt_in: bool = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

def hash_password(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, password_hash = hashed_password.split(':')
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash == computed_hash.hex()
    except:
        return False

@router.post("/register", response_model=LoginResponse)
async def register_user(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with trial subscription"""
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists. Please use the login page."
            )
        
        # Hash the password
        password_hash = hash_password(request.password)
        
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        
        # Create user in database
        user = User(
            email=request.email,
            name=f"{request.first_name} {request.last_name}",
            first_name=request.first_name,
            last_name=request.last_name,
            institution_name=request.institution_name,
            password_hash=password_hash,
            role=request.role,
            phone=request.phone,
            newsletter_opt_in=request.newsletter_opt_in,
            api_key=api_key,
            plan=request.plan,
            billing_period="monthly" if "monthly" in request.plan else "yearly",
            is_active=True,
            is_trial=True,
            trial_end=datetime.utcnow() + timedelta(days=7),
            trial_expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        # For now, create mock Stripe IDs (in production, integrate with actual Stripe)
        user.customer_id = f"cus_{secrets.token_hex(8)}"
        user.subscription_id = None  # Will be set when they add payment method
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Generate JWT token
        access_token = create_jwt_token(user.email)
        
        logger.info(f"User registered successfully: {request.email}")
        
        return LoginResponse(
            success=True,
            message="Registration successful! Your 7-day trial has started.",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "api_key": user.api_key,
                "user": {
                    "id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "institution_name": user.institution_name,
                    "plan": user.plan,
                    "billing_period": user.billing_period,
                    "is_trial": user.is_trial,
                    "trial_end": user.trial_end.isoformat() if user.trial_end else None
                },
                "customer_id": user.customer_id,
                "subscription_id": user.subscription_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    try:
        # Find user in database
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Account is disabled. Please contact support."
            )
        
        # Check if trial has expired
        if user.is_trial and not user.is_trial_active:
            raise HTTPException(
                status_code=402,
                detail="Your trial has expired. Please upgrade to continue."
            )
        
        # Generate new JWT token
        access_token = create_jwt_token(user.email)
        
        # Generate new API key if needed
        if not user.api_key:
            user.api_key = secrets.token_urlsafe(32)
            await db.commit()
        
        logger.info(f"User logged in successfully: {request.email}")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "api_key": user.api_key,
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "plan": user.plan,
                "customer_id": user.customer_id,
                "subscription_id": user.subscription_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/verify-token")
async def verify_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify if a token is valid and return user info"""
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Find user
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "valid": True,
            "user_id": user.user_id,
            "email": user.email
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=500, detail="Token verification failed")

# Backward compatibility endpoints
@router.post("/register-trial", response_model=LoginResponse)
async def register_trial_user(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Backward compatibility endpoint - redirects to /register"""
    return await register_user(request, db)
