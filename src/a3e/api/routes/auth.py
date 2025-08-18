"""
Authentication API routes for user registration, login, and password management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets
import time
from datetime import datetime, timedelta
import jwt
from ...core.auth import generate_secure_token
from ...services.payment_service import PaymentService
from ...services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserRegistrationRequest(BaseModel):
    name: str
    institution_name: str
    email: EmailStr
    password: str
    role: str
    plan: str
    phone: Optional[str] = ""
    newsletter_opt_in: bool = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# In-memory user storage (In production, use a proper database)
users_db = {}
password_reset_tokens = {}

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

@router.post("/register-trial", response_model=LoginResponse)
async def register_trial_user(request: UserRegistrationRequest):
    """
    Register a new user with trial subscription
    """
    try:
        # Check if user already exists
        if request.email in users_db:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists. Please use the login page."
            )
        
        # Hash the password
        password_hash = hash_password(request.password)
        
        # Create trial subscription with Stripe
        payment_service = PaymentService()
        trial_result = await payment_service.create_trial_subscription(
            email=request.email,
            plan=request.plan,
            payment_method_id=None,  # No payment method for trial
            coupon_code=None
        )
        
        if not trial_result['success']:
            raise HTTPException(status_code=400, detail=trial_result['error'])
        
        # Store user in database
        user_id = f"user_{int(time.time())}_{len(users_db)}"
        users_db[request.email] = {
            'user_id': user_id,
            'name': request.name,
            'institution_name': request.institution_name,
            'email': request.email,
            'password_hash': password_hash,
            'role': request.role,
            'phone': request.phone,
            'newsletter_opt_in': request.newsletter_opt_in,
            'api_key': trial_result['api_key'],
            'customer_id': trial_result['customer_id'],
            'subscription_id': trial_result['subscription_id'],
            'plan': request.plan,
            'created_at': datetime.utcnow(),
            'trial_end': trial_result['trial_end']
        }
        
        logger.info(f"User registered successfully: {request.email}")
        
        return LoginResponse(
            success=True,
            message="Account created successfully",
            data={
                'user_id': user_id,
                'api_key': trial_result['api_key'],
                'trial_id': trial_result.get('customer_id'),  # Using customer_id as trial_id
                'customer_id': trial_result['customer_id'],
                'subscription_id': trial_result['subscription_id'],
                'plan': request.plan,
                'trial_end': trial_result['trial_end']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login_user(request: LoginRequest):
    """
    Authenticate user and return API key
    """
    try:
        # Check if user exists
        if request.email not in users_db:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        user = users_db[request.email]
        
        # Verify password
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Check if subscription is still active
        payment_service = PaymentService()
        account_status = await payment_service.get_account_status(user['api_key'])
        
        if not account_status or account_status['status'] in ['expired', 'suspended']:
            raise HTTPException(
                status_code=402,
                detail="Your subscription has expired. Please renew your plan."
            )
        
        logger.info(f"User logged in successfully: {request.email}")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data={
                'user_id': user['user_id'],
                'api_key': user['api_key'],
                'customer_id': user['customer_id'],
                'subscription_id': user['subscription_id'],
                'plan': user['plan']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/password-reset", response_model=LoginResponse)
async def request_password_reset(request: PasswordResetRequest):
    """
    Send password reset email
    """
    try:
        # Check if user exists
        if request.email not in users_db:
            # For security, don't reveal if email exists or not
            return LoginResponse(
                success=True,
                message="If an account with that email exists, a password reset link has been sent."
            )
        
        # Generate reset token
        reset_token = generate_secure_token(32)
        password_reset_tokens[reset_token] = {
            'email': request.email,
            'expires_at': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        }
        
        # Send password reset email
        email_service = EmailService()
        reset_link = f"https://mapmystandards.ai/reset-password?token={reset_token}"
        
        await email_service.send_password_reset_email(
            email=request.email,
            reset_link=reset_link,
            user_name=users_db[request.email]['name']
        )
        
        logger.info(f"Password reset requested for: {request.email}")
        
        return LoginResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.get("/user/{user_id}")
async def get_user_info(user_id: str, api_key: str = Depends()):
    """
    Get user information (protected endpoint)
    """
    try:
        # Find user by API key
        user = None
        for email, user_data in users_db.items():
            if user_data['api_key'] == api_key and user_data['user_id'] == user_id:
                user = user_data
                break
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return user info (without password hash)
        return {
            'user_id': user['user_id'],
            'name': user['name'],
            'institution_name': user['institution_name'],
            'email': user['email'],
            'role': user['role'],
            'phone': user['phone'],
            'plan': user['plan'],
            'created_at': user['created_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user information")
