"""
Authentication and Authorization for A³E API
Handles API key validation and user authentication
"""

from fastapi import HTTPException, status, Header
from typing import Optional
import hashlib
import time
from ..services.payment_service import PaymentService
import logging

logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key and return account information"""
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header."
        )
    
    # Validate API key format
    if not x_api_key.startswith("a3e_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    try:
        # Check API key with payment service
        payment_service = PaymentService()
        account = await payment_service.get_account_status(x_api_key)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check account status
        if account["status"] == "expired":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Account expired. Please upgrade to continue using the API."
            )
        
        if account["status"] == "suspended":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended. Please contact support."
            )
        
        # Track API usage
        usage_allowed = await payment_service.track_api_usage(x_api_key, "api_call")
        
        if not usage_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API quota exceeded. Please upgrade your plan."
            )
        
        return x_api_key
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

async def verify_admin_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify admin API key for administrative operations"""
    
    api_key = await verify_api_key(x_api_key)
    
    # Check if this is an admin key
    payment_service = PaymentService()
    account = await payment_service.get_account_status(api_key)
    
    if account["plan"] != "enterprise" or account.get("admin_privileges") != True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return api_key

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    import secrets
    return secrets.token_urlsafe(length)

def hash_password(password: str) -> str:
    """Hash a password securely"""
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed within rate limit"""
        now = time.time()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items() 
            if now - v["timestamp"] < window
        }
        
        if key not in self.requests:
            self.requests[key] = {"count": 1, "timestamp": now}
            return True
        
        if now - self.requests[key]["timestamp"] >= window:
            self.requests[key] = {"count": 1, "timestamp": now}
            return True
        
        if self.requests[key]["count"] >= limit:
            return False
        
        self.requests[key]["count"] += 1
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract API key from request
            api_key = kwargs.get("api_key") or "anonymous"
            
            if not rate_limiter.is_allowed(api_key, limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
