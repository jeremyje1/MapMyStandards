"""
Authentication implementation for A3E platform
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
import bcrypt
import logging
import secrets
import uuid
import hashlib

from ...models.user import User, UserSession
from ...services.database_service import DatabaseService
from ...core.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
settings = get_settings()
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT settings (use environment variables in production)
JWT_SECRET = settings.jwt_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    success: bool
    message: str

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, name: str = None, remember: bool = False) -> str:
    """Create JWT token for authenticated user with UUID
    
    Args:
        user_id: The user's UUID from the database
        email: The user's email address
        name: The user's name (optional)
        remember: Whether to create a longer-lived token
    """
    expiration = timedelta(hours=JWT_EXPIRATION_HOURS * (30 if remember else 1))
    expire = datetime.utcnow() + expiration
    
    payload = {
        "sub": str(user_id),  # Use UUID as the subject
        "user_id": str(user_id),  # Explicit user_id field with UUID
        "email": email,  # Keep email for display/reference
        "name": name,  # Include name for UI if provided
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _candidate_secrets() -> list:
    from os import getenv
    # Try common keys to handle legacy tokens
    return [
        settings.jwt_secret_key,
        getattr(settings, 'secret_key', None),
        getenv('JWT_SECRET_KEY'),
        getenv('SECRET_KEY'),
        'your-secret-key-here-change-in-production',
    ]

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload if valid. Tries multiple secrets.
    
    Returns:
        Dict containing user information if valid, None otherwise
    """
    for secret in _candidate_secrets():
        if not secret:
            continue
        try:
            payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
            # Return the full payload to support both old (email) and new (UUID) tokens
            return payload
        except Exception:
            continue
    logger.warning("JWT verification failed for all candidate secrets")
    return None


def verify_jwt_token_email(token: str) -> Optional[str]:
    """Verify JWT token and return email if valid (backward compatibility).
    
    This is a compatibility wrapper that extracts the email from the token payload.
    It supports both old tokens (email in 'sub') and new tokens (email in 'email' field).
    """
    payload = verify_jwt_token(token)
    if payload:
        # Try to get email from the 'email' field first (new format)
        # Fall back to 'sub' field for old tokens that used email as subject
        return payload.get("email", payload.get("sub"))
    return None

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token
    """
    try:
        # Get user from database
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Check if user exists
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
                detail="Account is disabled"
            )
        
        # Check if trial is expired
        if user.is_trial and not user.is_trial_active:
            raise HTTPException(
                status_code=403,
                detail="Your trial has expired. Please upgrade to continue."
            )
        
        # Create JWT token with session tracking
        jti = str(uuid.uuid4())
        token = create_jwt_token(str(user.id), user.email, user.name, request.remember)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            token_jti=jti,
            expires_at=datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS * (30 if request.remember else 1))
        )
        db.add(session)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        await db.commit()
        
        # Return user data (excluding sensitive info)
        user_info = {
            "email": user.email,
            "name": user.name,
            "institution_name": user.institution_name,
            "role": user.role,
            "plan": user.subscription_tier,
            "trial_id": str(user.id),
            "expires_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None
        }
        
        logger.info(f"Successful login for {request.email}")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            token=token,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Authentication failed. Please try again."
        )

@router.post("/logout")
async def logout():
    """
    Logout user (client should delete token)
    """
    return {
        "success": True,
        "message": "Logged out successfully"
    }

@router.post("/verify-token")
async def verify_token(token: str):
    """
    Verify if a JWT token is valid
    """
    payload = verify_jwt_token(token)
    if payload:
        # Handle both old (email in sub) and new (UUID in sub) token formats
        email = payload.get("email", payload.get("sub"))
        user_id = payload.get("user_id", payload.get("sub"))
        return {
            "valid": True,
            "email": email,
            "user_id": user_id
        }
    else:
        return {
            "valid": False,
            "email": None,
            "user_id": None
        }

@router.post("/password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email
    """
    try:
        # Get user from database
        stmt = select(User).where(User.email == request.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return PasswordResetResponse(
                success=True,
                message="If an account exists with this email, you will receive password reset instructions."
            )
        
        # Generate reset token and code
        reset_token = secrets.token_urlsafe(32)
        reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Create password reset record
        from ...models.user import PasswordReset
        
        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=reset_token,
            reset_code=reset_code,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(password_reset)
        await db.commit()
        
        # Send reset email
        from ...services.email_service import email_service
        
        reset_link = f"https://mapmystandards.ai/reset-password?token={reset_token}"
        
        # Use enhanced password reset email
        await email_service.send_enhanced_password_reset_email(
            recipient_email=user.email,
            user_name=user.name,
            reset_link=reset_link,
            reset_code=reset_code,
            request_time=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC"),
            expiry_hours=1
        )
        
        logger.info(f"Password reset requested for {request.email}")
        
        return PasswordResetResponse(
            success=True,
            message="If an account exists with this email, you will receive password reset instructions."
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process password reset request."
        )
