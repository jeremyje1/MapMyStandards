"""Workspace service for team collaboration features."""
import uuid
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.workspace import (
    Workspace, WorkspaceRole, WorkspaceInvitation,
    StandardWorkspace, EvidenceWorkspace, workspace_members
)
from ..models.user import User
from .email_service import EmailService
import secrets

class WorkspaceService:
    """Service for managing workspaces and team collaboration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_workspace(self, user_id: str, name: str, description: str = None, 
                        institution_id: str = None) -> Workspace:
        """Create a new workspace with the creator as owner."""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            institution_id=institution_id
        )
        self.db.add(workspace)
        self.db.flush()
        
        # Add creator as owner
        self.db.execute(
            workspace_members.insert().values(
                workspace_id=workspace.id,
                user_id=user_id,
                role=WorkspaceRole.OWNER,
                invitation_accepted=True
            )
        )
        self.db.commit()
        return workspace
    
    def get_user_workspaces(self, user_id: str) -> List[Dict]:
        """Get all workspaces a user belongs to."""
        result = self.db.execute(
            workspace_members.select().where(
                workspace_members.c.user_id == user_id
            )
        ).fetchall()
        
        workspaces = []
        for row in result:
            workspace = self.db.query(Workspace).filter_by(id=row.workspace_id).first()
            if workspace and workspace.is_active:
                workspaces.append({
                    'workspace': workspace,
                    'role': row.role,
                    'joined_at': row.joined_at
                })
        return workspaces
    
    def invite_user(self, workspace_id: str, inviter_id: str, email: str, 
                   role: WorkspaceRole) -> WorkspaceInvitation:
        """Invite a user to join a workspace."""
        # Check if inviter has permission
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace or not workspace.can_user_manage(inviter_id):
            raise PermissionError("You don't have permission to invite users to this workspace")
        
        # Check if user already exists and is a member
        existing_user = self.db.query(User).filter_by(email=email).first()
        if existing_user:
            existing_member = self.db.execute(
                workspace_members.select().where(
                    (workspace_members.c.workspace_id == workspace_id)
                    & (workspace_members.c.user_id == existing_user.id)
                )
            ).first()
            if existing_member:
                raise ValueError("User is already a member of this workspace")
        
        # Create invitation
        invitation = WorkspaceInvitation(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            email=email,
            role=role,
            invited_by=inviter_id,
            invitation_token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(invitation)
        self.db.commit()
        
        # Send invitation email
        self._send_invitation_email(invitation, workspace)
        return invitation
    
    def accept_invitation(self, invitation_token: str, user_id: str) -> Workspace:
        """Accept a workspace invitation."""
        invitation = self.db.query(WorkspaceInvitation).filter_by(
            invitation_token=invitation_token
        ).first()
        
        if not invitation:
            raise ValueError("Invalid invitation")
        
        if invitation.status != "pending":
            raise ValueError("Invitation already used")
        
        if invitation.expires_at < datetime.utcnow():
            invitation.status = "expired"
            self.db.commit()
            raise ValueError("Invitation has expired")
        
        # Add user to workspace
        self.db.execute(
            workspace_members.insert().values(
                workspace_id=invitation.workspace_id,
                user_id=user_id,
                role=invitation.role,
                invited_by=invitation.invited_by,
                invitation_accepted=True
            )
        )
        
        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        self.db.commit()
        
        return self.db.query(Workspace).filter_by(id=invitation.workspace_id).first()
    
    def add_standard_to_workspace(self, workspace_id: str, standard_id: str, 
                                 user_id: str, notes: str = None, 
                                 priority: str = "medium") -> StandardWorkspace:
        """Add a standard to a workspace."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace or not workspace.can_user_edit(user_id):
            raise PermissionError("You don't have permission to add standards to this workspace")
        
        # Check if already exists
        existing = self.db.query(StandardWorkspace).filter_by(
            workspace_id=workspace_id,
            standard_id=standard_id
        ).first()
        
        if existing:
            # Update existing
            existing.notes = notes or existing.notes
            existing.priority = priority
            self.db.commit()
            return existing
        
        # Create new
        standard_workspace = StandardWorkspace(
            id=str(uuid.uuid4()),
            standard_id=standard_id,
            workspace_id=workspace_id,
            added_by=user_id,
            notes=notes,
            priority=priority
        )
        self.db.add(standard_workspace)
        self.db.commit()
        return standard_workspace
    
    def add_evidence_to_workspace(self, workspace_id: str, evidence_id: str, 
                                 user_id: str) -> EvidenceWorkspace:
        """Add evidence to a workspace."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace or not workspace.can_user_edit(user_id):
            raise PermissionError("You don't have permission to add evidence to this workspace")
        
        # Check if already exists
        existing = self.db.query(EvidenceWorkspace).filter_by(
            workspace_id=workspace_id,
            evidence_id=evidence_id
        ).first()
        
        if existing:
            return existing
        
        # Create new
        evidence_workspace = EvidenceWorkspace(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            workspace_id=workspace_id,
            added_by=user_id
        )
        self.db.add(evidence_workspace)
        self.db.commit()
        return evidence_workspace
    
    def review_evidence(self, workspace_id: str, evidence_id: str, user_id: str,
                       status: str, notes: str = None) -> EvidenceWorkspace:
        """Review evidence in a workspace."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace or not workspace.can_user_manage(user_id):
            raise PermissionError("You don't have permission to review evidence in this workspace")
        
        evidence_workspace = self.db.query(EvidenceWorkspace).filter_by(
            workspace_id=workspace_id,
            evidence_id=evidence_id
        ).first()
        
        if not evidence_workspace:
            raise ValueError("Evidence not found in workspace")
        
        evidence_workspace.review_status = status
        evidence_workspace.reviewed_by = user_id
        evidence_workspace.reviewed_at = datetime.utcnow()
        evidence_workspace.review_notes = notes
        self.db.commit()
        return evidence_workspace
    
    def update_user_role(self, workspace_id: str, user_id: str, 
                        target_user_id: str, new_role: WorkspaceRole):
        """Update a user's role in a workspace."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Check permissions
        user_role = workspace.get_user_role(user_id)
        if user_role != WorkspaceRole.OWNER and user_role != WorkspaceRole.ADMIN:
            raise PermissionError("You don't have permission to change user roles")
        
        # Can't change owner's role
        target_role = workspace.get_user_role(target_user_id)
        if target_role == WorkspaceRole.OWNER:
            raise PermissionError("Cannot change the owner's role")
        
        # Update role
        self.db.execute(
            workspace_members.update().where(
                (workspace_members.c.workspace_id == workspace_id)
                & (workspace_members.c.user_id == target_user_id)
            ).values(role=new_role)
        )
        self.db.commit()
    
    def remove_user(self, workspace_id: str, user_id: str, target_user_id: str):
        """Remove a user from a workspace."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Check permissions
        user_role = workspace.get_user_role(user_id)
        if user_role != WorkspaceRole.OWNER and user_role != WorkspaceRole.ADMIN:
            raise PermissionError("You don't have permission to remove users")
        
        # Can't remove owner
        target_role = workspace.get_user_role(target_user_id)
        if target_role == WorkspaceRole.OWNER:
            raise PermissionError("Cannot remove the owner")
        
        # Remove user
        self.db.execute(
            workspace_members.delete().where(
                (workspace_members.c.workspace_id == workspace_id)
                & (workspace_members.c.user_id == target_user_id)
            )
        )
        self.db.commit()
    
    def delete_workspace(self, workspace_id: str, user_id: str):
        """Delete a workspace (owner only)."""
        workspace = self.db.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Only owner can delete
        user_role = workspace.get_user_role(user_id)
        if user_role != WorkspaceRole.OWNER:
            raise PermissionError("Only the workspace owner can delete it")
        
        # Soft delete
        workspace.is_active = False
        self.db.commit()
    
    def _send_invitation_email(self, invitation: WorkspaceInvitation, workspace: Workspace):
        """Send workspace invitation email."""
        inviter = self.db.query(User).filter_by(id=invitation.invited_by).first()
        
        subject = f"You're invited to join {workspace.name} on MapMyStandards"
        body = f"""
Hi there,

{inviter.name} has invited you to join the workspace "{workspace.name}" on MapMyStandards.

Role: {invitation.role.value}

Click the link below to accept the invitation:
https://app.mapmystandards.com/accept-invitation?token={invitation.invitation_token}

This invitation will expire in 7 days.

Best regards,
MapMyStandards Team
"""
        
        # For now, just print the email (implement proper email service later)
        print(f"Would send email to {invitation.email}: {subject}")
        # TODO: EmailService().send_email(invitation.email, subject, body)