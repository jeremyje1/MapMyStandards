from typing import Dict
"""
Team management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...database.enterprise_models import Team, TeamInvitation, UserRole
from ...services.team_service import TeamService
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
class TeamCreate(BaseModel):
    name: str = Field(..., description="Team name")
    description: Optional[str] = Field(None, description="Team description")

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    settings: Optional[dict] = Field(None, description="Team settings")

class TeamInvite(BaseModel):
    email: str = Field(..., description="Email to invite")
    role: str = Field("viewer", description="Role for new member")

class RoleUpdate(BaseModel):
    role: str = Field(..., description="New role for member")

class TeamResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    created_at: str
    member_count: int
    user_role: str

class TeamMemberResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    joined_at: str

class InvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    expires_at: str
    invitation_url: str

# Routes
@router.post("", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db)
):
    """Create a new team"""
    team = await TeamService.create_team(
        db=db,
        name=team_data.name,
        owner_id=current_user.get("id"),
        description=team_data.description
    )
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="create",
        resource_type="team",
        team_id=team.id,
        resource_id=team.id,
        ip_address=request.client.host if request.client else None
    )
    
    members = await TeamService.get_team_members(db, team.id)
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        created_at=team.created_at.isoformat(),
        member_count=len(members),
        user_role=UserRole.OWNER.value
    )

@router.get("", response_model=List[TeamResponse])
async def get_my_teams(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all teams for current user"""
    user_teams = await TeamService.get_user_teams(db, current_user.get("id"))
    
    response = []
    for team_data in user_teams:
        team = team_data["team"]
        members = await TeamService.get_team_members(db, team.id)
        
        response.append(TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            created_at=team.created_at.isoformat(),
            member_count=len(members),
            user_role=team_data["role"]
        ))
    
    return response

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team details"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "read"
    )
    
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    members = await TeamService.get_team_members(db, team.id)
    user_role = await TeamService.get_user_role_in_team(db, team_id, current_user.get("id"))
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        created_at=team.created_at.isoformat(),
        member_count=len(members),
        user_role=user_role
    )

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update team details"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "manage"
    )
    
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Track changes
    changes = {}
    
    if team_update.name is not None:
        changes["name"] = {"old": team.name, "new": team_update.name}
        team.name = team_update.name
    
    if team_update.description is not None:
        changes["description"] = {"old": team.description, "new": team_update.description}
        team.description = team_update.description
    
    if team_update.settings is not None:
        changes["settings"] = {"old": team.settings, "new": team_update.settings}
        team.settings = team_update.settings
    
    await db.commit()
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="update",
        resource_type="team",
        team_id=team_id,
        resource_id=team_id,
        changes=changes,
        ip_address=request.client.host if request.client else None
    )
    
    members = await TeamService.get_team_members(db, team_id)
    user_role = await TeamService.get_user_role_in_team(db, team_id, current_user.get("id"))
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        created_at=team.created_at.isoformat(),
        member_count=len(members),
        user_role=user_role
    )

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team members"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "read"
    )
    
    members = await TeamService.get_team_members(db, team_id)
    
    response = []
    for member_data in members:
        user = member_data["user"]
        response.append(TeamMemberResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=member_data["role"],
            joined_at=member_data["joined_at"].isoformat()
        ))
    
    return response

@router.post("/{team_id}/invite", response_model=InvitationResponse)
async def invite_member(
    team_id: str,
    invite_data: TeamInvite,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new member to the team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "manage"
    )
    
    # Validate role
    try:
        role = UserRole(invite_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    invitation = await TeamService.invite_member(
        db=db,
        team_id=team_id,
        email=invite_data.email,
        role=role,
        invited_by_id=current_user.get("id")
    )
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="invite",
        resource_type="team",
        team_id=team_id,
        resource_id=invitation.id,
        changes={"email": invite_data.email, "role": role.value},
        ip_address=request.client.host if request.client else None
    )
    
    # Build invitation URL
    base_url = settings.frontend_url or "https://platform.mapmystandards.ai"
    invitation_url = f"{base_url}/accept-invite?token={invitation.token}"
    
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role.value,
        expires_at=invitation.expires_at.isoformat(),
        invitation_url=invitation_url
    )

@router.put("/{team_id}/members/{user_id}/role", response_model=dict)
async def update_member_role(
    team_id: str,
    user_id: str,
    role_update: RoleUpdate,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a team member's role"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "manage"
    )
    
    # Validate role
    try:
        new_role = UserRole(role_update.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    # Don't allow changing own role if user is the only owner
    if user_id == current_user.get("id") and new_role != UserRole.OWNER:
        members = await TeamService.get_team_members(db, team_id)
        owner_count = sum(1 for m in members if m["role"] == UserRole.OWNER.value)
        if owner_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role - team must have at least one owner"
            )
    
    old_role = await TeamService.get_user_role_in_team(db, team_id, user_id)
    await TeamService.update_member_role(db, team_id, user_id, new_role)
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="update",
        resource_type="team_member",
        team_id=team_id,
        resource_id=user_id,
        changes={"role": {"old": old_role, "new": new_role.value}},
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "new_role": new_role.value}

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from the team"""
    await EnhancedAuthService.require_team_permission(
        db, current_user.get("id"), team_id, "manage"
    )
    
    # Don't allow removing self if user is the only owner
    if user_id == current_user.get("id"):
        members = await TeamService.get_team_members(db, team_id)
        owner_count = sum(1 for m in members if m["role"] == UserRole.OWNER.value)
        if owner_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself - team must have at least one owner"
            )
    
    await TeamService.remove_member(db, team_id, user_id)
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="remove",
        resource_type="team_member",
        team_id=team_id,
        resource_id=user_id,
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True}

@router.post("/accept-invite")
async def accept_invitation(
    token: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a team invitation"""
    team = await TeamService.accept_invitation(db, token, current_user.get("id"))
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation"
        )
    
    # Log action
    await AuditService.log_action(
        db=db,
        user_id=current_user.get("id"),
        action="join",
        resource_type="team",
        team_id=team.id,
        resource_id=team.id,
        ip_address=request.client.host if request.client else None
    )
    
    return {"success": True, "team_id": team.id, "team_name": team.name}
