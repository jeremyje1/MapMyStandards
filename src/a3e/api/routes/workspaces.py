"""Workspace API routes for team collaboration."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, AsyncGenerator
from pydantic import BaseModel
from datetime import datetime
import logging

from ..dependencies import get_current_user
from ...services.workspace_service import WorkspaceService
from ...models.workspace import WorkspaceRole
from ...core.config import settings
from ...services.database_service import DatabaseService

logger = logging.getLogger(__name__)

# Database dependency
_db_service: Optional['DatabaseService'] = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency function"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(settings.database_url)
    async with _db_service.get_session() as session:
        yield session

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

# Pydantic models
class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    institution_id: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    institution_id: Optional[str]
    is_active: bool
    created_at: datetime
    member_count: int
    user_role: str

class InvitationCreate(BaseModel):
    email: str
    role: str  # owner, admin, editor, viewer

class InvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    invited_by_name: str
    created_at: datetime
    expires_at: datetime
    status: str

class StandardAdd(BaseModel):
    standard_id: str
    notes: Optional[str] = None
    priority: str = "medium"

class EvidenceAdd(BaseModel):
    evidence_id: str

class EvidenceReview(BaseModel):
    status: str  # approved, rejected
    notes: Optional[str] = None

class RoleUpdate(BaseModel):
    role: str

# Routes
@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace."""
    service = WorkspaceService(db)
    workspace = service.create_workspace(
        user_id=current_user["user_id"],
        name=workspace_data.name,
        description=workspace_data.description,
        institution_id=workspace_data.institution_id or current_user.get("institution_id")
    )
    
    # Get member count
    members = db.execute(
        "SELECT COUNT(*) FROM workspace_members WHERE workspace_id = :workspace_id",
        {"workspace_id": workspace.id}
    ).scalar()
    
    return {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "institution_id": workspace.institution_id,
        "is_active": workspace.is_active,
        "created_at": workspace.created_at,
        "member_count": members,
        "user_role": WorkspaceRole.OWNER.value
    }

@router.get("", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all workspaces the user belongs to."""
    service = WorkspaceService(db)
    user_workspaces = service.get_user_workspaces(current_user["user_id"])
    
    responses = []
    for uw in user_workspaces:
        workspace = uw['workspace']
        members = db.execute(
            "SELECT COUNT(*) FROM workspace_members WHERE workspace_id = :workspace_id",
            {"workspace_id": workspace.id}
        ).scalar()
        
        responses.append({
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "institution_id": workspace.institution_id,
            "is_active": workspace.is_active,
            "created_at": workspace.created_at,
            "member_count": members,
            "user_role": uw['role'].value
        })
    
    return responses

@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspace details with members and content."""
    from ...models.workspace import Workspace, workspace_members
    
    workspace = db.query(Workspace).filter_by(id=workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if user is a member
    user_role = workspace.get_user_role(current_user["user_id"])
    if not user_role:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    # Get members
    members_result = db.execute(
        """
        SELECT u.id, u.name, u.email, wm.role, wm.joined_at
        FROM workspace_members wm
        JOIN users u ON u.id = wm.user_id
        WHERE wm.workspace_id = :workspace_id
        """,
        {"workspace_id": workspace_id}
    ).fetchall()
    
    members = [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "joined_at": m.joined_at
        }
        for m in members_result
    ]
    
    # Get standards count
    standards_count = db.execute(
        "SELECT COUNT(*) FROM standard_workspaces WHERE workspace_id = :workspace_id",
        {"workspace_id": workspace_id}
    ).scalar()
    
    # Get evidence count
    evidence_count = db.execute(
        "SELECT COUNT(*) FROM evidence_workspaces WHERE workspace_id = :workspace_id",
        {"workspace_id": workspace_id}
    ).scalar()
    
    return {
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "institution_id": workspace.institution_id,
            "is_active": workspace.is_active,
            "created_at": workspace.created_at,
            "allow_guest_access": workspace.allow_guest_access,
            "require_approval": workspace.require_approval
        },
        "user_role": user_role.value,
        "members": members,
        "stats": {
            "member_count": len(members),
            "standards_count": standards_count,
            "evidence_count": evidence_count
        }
    }

@router.post("/{workspace_id}/invite", response_model=InvitationResponse)
async def invite_to_workspace(
    workspace_id: str,
    invitation: InvitationCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join the workspace."""
    service = WorkspaceService(db)
    
    # Convert role string to enum
    try:
        role = WorkspaceRole(invitation.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    try:
        invite = service.invite_user(
            workspace_id=workspace_id,
            inviter_id=current_user["user_id"],
            email=invitation.email,
            role=role
        )
        
        return {
            "id": invite.id,
            "email": invite.email,
            "role": invite.role.value,
            "invited_by_name": current_user.get("name", current_user["email"]),
            "created_at": invite.created_at,
            "expires_at": invite.expires_at,
            "status": invite.status
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/accept-invitation")
async def accept_invitation(
    token: str = Query(..., description="Invitation token"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a workspace invitation."""
    service = WorkspaceService(db)
    
    try:
        workspace = service.accept_invitation(token, current_user["user_id"])
        return {"message": f"Successfully joined workspace: {workspace.name}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workspace_id}/standards", status_code=201)
async def add_standard_to_workspace(
    workspace_id: str,
    standard_data: StandardAdd,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a standard to the workspace."""
    service = WorkspaceService(db)
    
    try:
        result = service.add_standard_to_workspace(
            workspace_id=workspace_id,
            standard_id=standard_data.standard_id,
            user_id=current_user["user_id"],
            notes=standard_data.notes,
            priority=standard_data.priority
        )
        return {"message": "Standard added to workspace", "id": result.id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{workspace_id}/evidence", status_code=201)
async def add_evidence_to_workspace(
    workspace_id: str,
    evidence_data: EvidenceAdd,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add evidence to the workspace."""
    service = WorkspaceService(db)
    
    try:
        result = service.add_evidence_to_workspace(
            workspace_id=workspace_id,
            evidence_id=evidence_data.evidence_id,
            user_id=current_user["user_id"]
        )
        return {"message": "Evidence added to workspace", "id": result.id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.put("/{workspace_id}/evidence/{evidence_id}/review")
async def review_workspace_evidence(
    workspace_id: str,
    evidence_id: str,
    review_data: EvidenceReview,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Review evidence in a workspace."""
    service = WorkspaceService(db)
    
    try:
        result = service.review_evidence(
            workspace_id=workspace_id,
            evidence_id=evidence_id,
            user_id=current_user["user_id"],
            status=review_data.status,
            notes=review_data.notes
        )
        return {"message": f"Evidence {review_data.status}", "reviewed_at": result.reviewed_at}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    workspace_id: str,
    user_id: str,
    role_data: RoleUpdate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a member's role in the workspace."""
    service = WorkspaceService(db)
    
    try:
        role = WorkspaceRole(role_data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    try:
        service.update_user_role(
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            target_user_id=user_id,
            new_role=role
        )
        return {"message": f"User role updated to {role.value}"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the workspace."""
    service = WorkspaceService(db)
    
    try:
        service.remove_user(
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            target_user_id=user_id
        )
        return {"message": "User removed from workspace"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workspace (soft delete)."""
    service = WorkspaceService(db)
    
    try:
        service.delete_workspace(workspace_id, current_user["user_id"])
        return {"message": "Workspace deleted successfully"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))