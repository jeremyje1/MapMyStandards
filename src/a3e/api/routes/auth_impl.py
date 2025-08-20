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

from ...models.user import User, UserSession
from ...services.database_service import DatabaseService
from ...core.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
settings = get_settings()
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = settings.jwt_secret_key if hasattr(settings, 'jwt_secret_key') else "your-secret-key-change-in-production"
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
JWT_SECRET = "your-secret-key-change-in-production"
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

def create_jwt_token(email: str, remember: bool = False) -> str:
    """Create JWT token for authenticated user"""
    expiration = timedelta(hours=JWT_EXPIRATION_HOURS * (30 if remember else 1))
    expire = datetime.utcnow() + expiration
    
    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify JWT token and return email if valid"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
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
        token = create_jwt_token(request.email, request.remember)
        
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
    email = verify_jwt_token(token)
    if email:
        return {
            "valid": True,
            "email": email
        }
    else:
        return {
            "valid": False,
            "email": None
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
