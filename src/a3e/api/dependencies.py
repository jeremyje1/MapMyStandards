"""
Common dependencies for API routes
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging
from typing import Optional, Dict

from ..core.config import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Validate JWT token and return current user info
    """
    try:
        token = credentials.credentials
        
        # Handle demo/test tokens
        if token == "demo_api_key_123":
            return {
                "user_id": "demo_user",
                "email": "demo@example.com",
                "name": "Demo User",
                "plan": "professional"
            }
        
        # Decode JWT token
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            
            return {
                "user_id": payload.get("user_id", payload.get("sub")),
                "email": payload.get("sub"),
                "name": payload.get("name", payload.get("sub", "").split("@")[0]),
                "plan": payload.get("plan", "trial")
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    Get current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except:
        return None

def has_active_subscription(current_user: Dict = Depends(get_current_user)):
    """
    Check if user has an active subscription (single $199/mo plan)
    """
    # Check if user has active subscription
    is_subscribed = current_user.get("subscription_status") == "active"
    is_trial = current_user.get("trial_status") == "active"
    
    if not is_subscribed and not is_trial:
        raise HTTPException(
            status_code=403,
            detail="This feature requires an active subscription. Subscribe for $199/month to access all features."
        )
    
    return current_user

# Legacy compatibility - all point to same check
require_professional = has_active_subscription
require_institution = has_active_subscription  
require_paid_plan = has_active_subscription
