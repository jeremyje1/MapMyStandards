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
optional_security = HTTPBearer(auto_error=False)

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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
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

async def get_optional_current_user(authorization: Optional[str] = None) -> Optional[Dict]:
    """
    Get current user without requiring authentication.
    Used for endpoints that should work for both authenticated and anonymous users.
    """
    if not authorization:
        return None
    
    try:
        # Extract bearer token
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            return await get_current_user(credentials)
    except:
        pass
    
    return None

def has_active_subscription(current_user: Dict = Depends(get_current_user)):
    """Return current user if they have access under subscription rules.

    Historical tokens only include a 'plan' field (e.g. 'trial', 'professional').
    Newer tokens may include explicit 'subscription_status' / 'trial_status'.
    To avoid blanket 403s for older tokens, we treat missing fields as an active trial.
    """
    subscription_status = current_user.get("subscription_status")
    trial_status = current_user.get("trial_status")
    plan = current_user.get("plan")

    # Derive flags
    is_subscribed = (
        subscription_status == "active" or plan in {"professional", "enterprise", "paid"}
    )
    is_trial = (
        trial_status == "active" or plan == "trial"
    )

    # If legacy token with neither status field, allow as trial to prevent false negatives
    if subscription_status is None and trial_status is None and plan is not None:
        is_trial = True

    if not (is_subscribed or is_trial):
        raise HTTPException(
            status_code=403,
            detail="Subscription required. Upgrade to access this feature."
        )
    return current_user

# Legacy compatibility - all point to same check
require_professional = has_active_subscription
require_institution = has_active_subscription  
require_paid_plan = has_active_subscription

# Database dependency
async def get_async_db():
    """Get async database session"""
    try:
        # Import here to avoid circular imports
        from ..database.connection import Database
        db = Database()
        async for session in db.get_session():
            yield session
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
