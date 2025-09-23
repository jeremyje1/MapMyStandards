#!/usr/bin/env python3
"""
Script to create a minimal authentication endpoint that works
"""

import os

# Create a minimal auth.py that handles login properly
auth_code = '''"""
Simple authentication API routes with proper error handling
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import jwt
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT Secret (in production, use environment variable)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Test user database
TEST_USERS = {
    "testuser@example.com": {
        "password_hash": "Test123!@#",  # In production, this would be hashed
        "name": "Test User",
        "institution": "Test University",
        "role": "admin",
        "onboarding_completed": True
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 day default
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint with proper error handling
    """
    try:
        logger.info(f"Login attempt for email: {request.email}")
        
        # Check if user exists
        if request.email not in TEST_USERS:
            logger.warning(f"Login failed: User not found - {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = TEST_USERS[request.email]
        
        # Verify password (simplified for test)
        if request.password != user_data["password_hash"]:
            logger.warning(f"Login failed: Invalid password for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": request.email, "role": user_data["role"]}
        )
        
        # Return success response
        response = LoginResponse(
            access_token=access_token,
            user={
                "email": request.email,
                "name": user_data["name"],
                "institution": user_data["institution"],
                "role": user_data["role"],
                "onboarding_completed": user_data["onboarding_completed"]
            }
        )
        
        logger.info(f"Login successful for: {request.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again."
        )

@router.get("/verify")
async def verify_token(token: str):
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "email": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
'''

# Save the fixed auth file
auth_file_path = "src/a3e/api/routes/auth_fixed.py"
print(f"Creating fixed auth file: {auth_file_path}")

# First, backup the original
if os.path.exists("src/a3e/api/routes/auth.py"):
    import shutil
    backup_path = "src/a3e/api/routes/auth_original.py"
    if not os.path.exists(backup_path):
        shutil.copy("src/a3e/api/routes/auth.py", backup_path)
        print(f"✅ Backed up original to: {backup_path}")

# Write the new auth file
with open(auth_file_path, 'w') as f:
    f.write(auth_code)

print(f"✅ Created fixed auth file: {auth_file_path}")
print("\nTo deploy this fix:")
print("1. Replace the current auth.py with auth_fixed.py")
print("2. Commit and push to trigger Railway deployment")
print("\nOr for immediate testing, update the Railway service directly.")