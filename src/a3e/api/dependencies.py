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

def require_plan(allowed_plans: list):
    """
    Dependency to require specific subscription plans
    """
    async def plan_checker(current_user: Dict = Depends(get_current_user)):
        user_plan = current_user.get("plan", "trial")
        
        if user_plan not in allowed_plans:
            raise HTTPException(
                status_code=403,
                detail=f"This feature requires one of these plans: {', '.join(allowed_plans)}"
            )
        
        return current_user
    
    return plan_checker

# Common plan dependencies
require_professional = require_plan(["professional", "institution", "enterprise"])
require_institution = require_plan(["institution", "enterprise"])
require_paid_plan = require_plan(["starter", "professional", "institution", "enterprise"])
