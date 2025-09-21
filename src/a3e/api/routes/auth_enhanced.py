"""
Enhanced Authentication API with JWT tokens and httpOnly cookies
"""

from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging
import os
from sqlalchemy.orm import Session

from ...models.user import User
from ...core.database import get_db
from ...services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
REFRESH_TOKEN_REMEMBER_DAYS = 30

# Password hasher
ph = PasswordHasher()

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    institution_name: Optional[str] = None
    role: Optional[str] = "User"
    phone: Optional[str] = None
    newsletter_opt_in: bool = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

# Token management
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, remember: bool = False):
    """Create JWT refresh token"""
    to_encode = data.copy()
    if remember:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_REMEMBER_DAYS)
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# API Routes
@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Register a new user with email verification optional"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password with argon2
        password_hash = ph.hash(request.password)
        
        # Create user
        user = User(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
            institution_name=request.institution_name,
            role=request.role,
            phone=request.phone,
            newsletter_opt_in=request.newsletter_opt_in,
            is_active=True,  # Auto-activate for now
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=".mapmystandards.ai",
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            domain=".mapmystandards.ai",
            path="/"
        )
        
        # TODO: Send welcome email
        
        return AuthResponse(
            success=True,
            message="Registration successful",
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login with email and password, returns httpOnly cookies"""
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        try:
            ph.verify(user.password_hash, request.password)
        except VerifyMismatchError:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is not active")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "email": user.email},
            remember=request.rememberMe
        )
        
        # Calculate cookie max age
        refresh_max_age = (REFRESH_TOKEN_REMEMBER_DAYS if request.rememberMe else REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=".mapmystandards.ai",
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=refresh_max_age,
            domain=".mapmystandards.ai",
            path="/"
        )
        
        # Store refresh token in database for revocation
        user.refresh_token = refresh_token
        user.refresh_token_expires = datetime.utcnow() + timedelta(seconds=refresh_max_age)
        db.commit()
        
        return AuthResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "institution_name": user.institution_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/request-password-reset", response_model=AuthResponse)
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset email with one-time token"""
    try:
        # Always return success for security (don't reveal if email exists)
        user = db.query(User).filter(User.email == request.email).first()
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store token with expiration
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.commit()
            
            # Send email
            email_service = EmailService()
            reset_link = f"https://api.mapmystandards.ai/reset-password?token={reset_token}"
            
            await email_service.send_password_reset_email(
                email=user.email,
                reset_link=reset_link,
                user_name=user.name
            )
            
            logger.info(f"Password reset requested for: {user.email}")
        
        return AuthResponse(
            success=True,
            message="If an account exists with that email, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Still return success for security
        return AuthResponse(
            success=True,
            message="If an account exists with that email, a password reset link has been sent."
        )

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(request: ResetPasswordRequest, response: Response, db: Session = Depends(get_db)):
    """Reset password using token from email"""
    try:
        # Find user by reset token
        user = db.query(User).filter(
            User.reset_token == request.token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Hash new password
        password_hash = ph.hash(request.password)
        
        # Update user
        user.password_hash = password_hash
        user.reset_token = None
        user.reset_token_expires = None
        user.refresh_token = None  # Revoke existing sessions
        user.refresh_token_expires = None
        db.commit()
        
        # Clear any existing cookies
        response.delete_cookie(key="access_token", domain=".mapmystandards.ai", path="/")
        response.delete_cookie(key="refresh_token", domain=".mapmystandards.ai", path="/")
        
        logger.info(f"Password reset successful for: {user.email}")
        
        return AuthResponse(
            success=True,
            message="Password reset successful. Please login with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using refresh token from cookie"""
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        user_id = payload.get("sub")
        
        # Find user and verify stored refresh token
        user = db.query(User).filter(
            User.id == user_id,
            User.refresh_token == refresh_token,
            User.refresh_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        new_access_token = create_access_token({"sub": str(user.id), "email": user.email})
        
        # Set new access token cookie
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=".mapmystandards.ai",
            path="/"
        )
        
        return AuthResponse(
            success=True,
            message="Token refreshed successfully",
            access_token=new_access_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(response: Response, db: Session = Depends(get_db), current_user: Dict = Depends(get_current_user)):
    """Logout user and clear cookies"""
    try:
        # Revoke refresh token in database
        current_user.refresh_token = None
        current_user.refresh_token_expires = None
        db.commit()
        
        # Clear cookies
        response.delete_cookie(key="access_token", domain=".mapmystandards.ai", path="/")
        response.delete_cookie(key="refresh_token", domain=".mapmystandards.ai", path="/")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.get("id")),
        "email": current_user.get("email"),
        "name": current_user.name,
        "role": current_user.get("role"),
        "institution_name": current_user.institution_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }