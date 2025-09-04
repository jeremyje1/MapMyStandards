"""
SSO (Single Sign-On) API endpoints
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.sso_service import SSOService
from ...services.database_service import DatabaseService
from ...services.audit_service import AuditService
from ...core.config import get_settings

router = APIRouter()
settings = get_settings()

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Pydantic models
class SSOInitiateResponse(BaseModel):
    auth_url: str
    state: str

class SSOProviderInfo(BaseModel):
    name: str
    enabled: bool
    icon: str

# Add current user dependency
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get current user from session token"""
    # Check for session token in cookie or Authorization header
    token = None
    
    # Check cookie
    if "session_token" in request.cookies:
        token = request.cookies["session_token"]
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Validate token and get user
    user = await SSOService.validate_session_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "role": getattr(user, "role", "user")
    }

# Routes
@router.get("/providers", response_model=Dict[str, SSOProviderInfo])
async def get_sso_providers():
    """Get available SSO providers"""
    providers = await SSOService.get_available_providers()
    return providers

@router.get("/initiate/{provider}")
async def initiate_sso(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    request: Request = None
):
    """Initiate SSO authentication flow"""
    # Default redirect URI if not provided
    if not redirect_uri:
        base_url = settings.frontend_url or "https://platform.mapmystandards.ai"
        redirect_uri = f"{base_url}/auth/sso/callback"
    
    try:
        result = await SSOService.initiate_sso(provider, redirect_uri)
        
        # Store state in session/cookie for verification
        # For now, we'll rely on the frontend to handle state
        
        return SSOInitiateResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO initialization failed"
        )

@router.get("/callback/{provider}")
async def sso_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: Optional[str] = Query(None),
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle SSO provider callback"""
    # Default redirect URI if not provided
    if not redirect_uri:
        base_url = settings.frontend_url or "https://platform.mapmystandards.ai"
        redirect_uri = f"{base_url}/auth/sso/callback"
    
    try:
        # Complete SSO flow
        user, session_token = await SSOService.complete_sso(
            db=db,
            provider_name=provider,
            code=code,
            state=state,
            redirect_uri=redirect_uri
        )
        
        # Log the SSO login
        await AuditService.log_action(
            db=db,
            user_id=user.id,
            action="login",
            resource_type="sso",
            resource_id=provider,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Set secure cookie with session token
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,  # Only over HTTPS
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        # Return success with redirect URL
        dashboard_url = f"{settings.frontend_url or 'https://platform.mapmystandards.ai'}/dashboard.html"
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            },
            "redirect_url": dashboard_url
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO authentication failed"
        )

class SSOConfiguration(BaseModel):
    provider: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    allowed_domains: Optional[list[str]] = None
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    certificate: Optional[str] = None

@router.post("/configure")
async def configure_sso(
    config: SSOConfiguration,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Configure SSO provider (admin only)"""
    if current_user.get("role") not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can configure SSO"
        )
    
    try:
        result = await SSOService.configure_provider(
            db=db,
            provider_name=config.provider,
            config=config.dict(exclude_unset=True)
        )
        
        # Log the configuration change
        await AuditService.log_action(
            db=db,
            user_id=current_user["id"],
            action="configure",
            resource_type="sso",
            resource_id=config.provider,
            details={"provider": config.provider}
        )
        
        return {"success": True, "message": f"{config.provider} SSO configured successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure SSO: {str(e)}"
        )

@router.get("/configurations")
async def get_sso_configurations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get SSO configurations (admin only)"""
    if current_user.get("role") not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view SSO configurations"
        )
    
    try:
        configurations = await SSOService.get_configurations(db)
        # Remove sensitive data
        for provider, config in configurations.items():
            if "client_secret" in config:
                config["client_secret"] = "***"
            if "certificate" in config and config["certificate"]:
                config["certificate"] = "*** REDACTED ***"
        
        return configurations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SSO configurations"
        )
