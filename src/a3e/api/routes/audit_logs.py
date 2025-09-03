"""
Audit logs API endpoints for tracking and compliance
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...services.audit_service import AuditService
from ...services.auth_service import EnhancedAuthService
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
class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: str
    user_email: str
    user_name: Optional[str]
    ip_address: Optional[str]
    created_at: str
    changes: Optional[dict]

class ActivitySummaryResponse(BaseModel):
    total_actions: int
    unique_users: int
    actions_by_type: dict
    resources_by_type: dict
    period_days: int

# Routes
@router.get("/teams/{team_id}/audit-logs", response_model=List[AuditLogResponse])
async def get_team_audit_logs(
    team_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for a team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "read"
    )
    
    logs = await AuditService.get_team_audit_logs(
        db=db,
        team_id=team_id,
        limit=limit,
        offset=offset,
        resource_type=resource_type,
        user_id=user_id
    )
    
    response = []
    for log in logs:
        # Get user info
        user = await db.get(User, log.user_id)
        
        description = AuditService.format_change_description(
            log.action, log.resource_type, log.changes
        )
        
        response.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=description,
            user_email=user.email if user else "Unknown",
            user_name=user.name if user else None,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat(),
            changes=log.changes
        ))
    
    return response

@router.get("/users/me/audit-logs", response_model=List[AuditLogResponse])
async def get_my_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for current user"""
    logs = await AuditService.get_user_audit_logs(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    response = []
    for log in logs:
        description = AuditService.format_change_description(
            log.action, log.resource_type, log.changes
        )
        
        response.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=description,
            user_email=current_user.email,
            user_name=current_user.name,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat(),
            changes=log.changes
        ))
    
    return response

@router.get("/resources/{resource_type}/{resource_id}/history", response_model=List[AuditLogResponse])
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    team_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get complete history for a specific resource"""
    # If team_id provided, check permission
    if team_id:
        await EnhancedAuthService.require_team_permission(
            db, current_user.id, team_id, "read"
        )
    
    logs = await AuditService.get_resource_history(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        team_id=team_id
    )
    
    response = []
    for log in logs:
        # Get user info
        user = await db.get(User, log.user_id)
        
        description = AuditService.format_change_description(
            log.action, log.resource_type, log.changes
        )
        
        response.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=description,
            user_email=user.email if user else "Unknown",
            user_name=user.name if user else None,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat(),
            changes=log.changes
        ))
    
    return response

@router.get("/teams/{team_id}/activity-summary", response_model=ActivitySummaryResponse)
async def get_team_activity_summary(
    team_id: str,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity summary for a team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.id, team_id, "read"
    )
    
    summary = await AuditService.get_activity_summary(
        db=db,
        team_id=team_id,
        days=days
    )
    
    return ActivitySummaryResponse(
        total_actions=summary["total_actions"],
        unique_users=summary["unique_users"],
        actions_by_type=summary["actions_by_type"],
        resources_by_type=summary["resources_by_type"],
        period_days=days
    )
