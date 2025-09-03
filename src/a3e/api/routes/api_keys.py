"""
API Key management endpoints
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...services.auth_service import EnhancedAuthService
from ...services.audit_service import AuditService
from ...services.database_service import DatabaseService
from ...core.config import get_settings

router = APIRouter()
settings = get_settings()

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Pydantic models
class ApiKeyCreate(BaseModel):
    name: str = Field(..., description="Name for the API key")
    scopes: List[str] = Field(["read"], description="Permissions for the API key")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: List[str]
    rate_limit: int
    active: bool
    last_used_at: Optional[str]
    expires_at: Optional[str]
    created_at: str

class ApiKeyCreateResponse(BaseModel):
    api_key: str
    key_info: ApiKeyResponse

# Routes
@router.get("/{team_id}/api-keys", response_model=List[ApiKeyResponse])
async def get_team_api_keys(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all API keys for a team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "manage"
    )
    
    api_keys = await EnhancedAuthService.get_team_api_keys(db, team_id)
    
    response = []
    for key in api_keys:
        response.append(ApiKeyResponse(
            id=key.id,
            name=key.name,
            prefix=key.prefix,
            scopes=key.scopes,
            rate_limit=key.rate_limit,
            active=key.active,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            created_at=key.created_at.isoformat()
        ))
    
    return response

@router.post("/{team_id}/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    team_id: str,
    key_data: ApiKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key for a team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "manage"
    )
    
    # Validate scopes
    valid_scopes = ["read", "write", "admin"]
    invalid_scopes = [scope for scope in key_data.scopes if scope not in valid_scopes]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {invalid_scopes}. Valid scopes: {valid_scopes}"
        )
    
    try:
        api_key, key_obj = await EnhancedAuthService.create_api_key(
            db=db,
            team_id=team_id,
            created_by_id=current_user.id,
            name=key_data.name,
            scopes=key_data.scopes,
            expires_in_days=key_data.expires_in_days
        )
        
        # Log action
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="create",
            resource_type="api_key",
            team_id=team_id,
            resource_id=key_obj.id,
            changes={"name": key_data.name, "scopes": key_data.scopes},
            ip_address=request.client.host if request.client else None
        )
        
        return ApiKeyCreateResponse(
            api_key=api_key,
            key_info=ApiKeyResponse(
                id=key_obj.id,
                name=key_obj.name,
                prefix=key_obj.prefix,
                scopes=key_obj.scopes,
                rate_limit=key_obj.rate_limit,
                active=key_obj.active,
                last_used_at=None,
                expires_at=key_obj.expires_at.isoformat() if key_obj.expires_at else None,
                created_at=key_obj.created_at.isoformat()
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )

@router.post("/{team_id}/api-keys/{key_id}/revoke")
async def revoke_api_key(
    team_id: str,
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "manage"
    )
    
    success = await EnhancedAuthService.revoke_api_key(db, key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        action="revoke",
        resource_type="api_key",
        team_id=team_id,
        resource_id=key_id,
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True}

@router.get("/{team_id}/api-keys/{key_id}/usage")
async def get_api_key_usage(
    team_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for an API key"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "manage"
    )
    
    # This would query your API usage logs
    # For now, return mock data
    return {
        "key_id": key_id,
        "current_month": {
            "requests": 156,
            "rate_limit": 1000,
            "usage_percentage": 15.6
        },
        "daily_usage": [
            {"date": "2025-09-01", "requests": 45},
            {"date": "2025-09-02", "requests": 67},
            {"date": "2025-09-03", "requests": 44}
        ]
    }
