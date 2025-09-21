"""Workspace models for team collaboration."""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class WorkspaceRole(enum.Enum):
    """Workspace role types."""
    OWNER = "owner"
    ADMIN = "admin" 
    EDITOR = "editor"
    VIEWER = "viewer"

# Association table for workspace members
workspace_members = Table(
    'workspace_members',
    Base.metadata,
    Column('workspace_id', String(36), ForeignKey('workspaces.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', Enum(WorkspaceRole), nullable=False),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    Column('invited_by', String(36), ForeignKey('users.id')),
    Column('invitation_accepted', Boolean, default=False)
)

class Workspace(Base):
    """Workspace model for team collaboration."""
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    institution_id = Column(String(36), ForeignKey('institutions.id'))
    
    # Workspace settings
    is_active = Column(Boolean, default=True)
    allow_guest_access = Column(Boolean, default=False)
    require_approval = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution", back_populates="workspaces")
    members = relationship("User", secondary=workspace_members, back_populates="workspaces")
    standards = relationship("StandardWorkspace", back_populates="workspace", cascade="all, delete-orphan")
    evidence = relationship("EvidenceWorkspace", back_populates="workspace", cascade="all, delete-orphan")
    
    def get_user_role(self, user_id):
        """Get a user's role in the workspace."""
        result = Base.metadata.tables['workspace_members'].select().where(
            (Base.metadata.tables['workspace_members'].c.workspace_id == self.id)
            & (Base.metadata.tables['workspace_members'].c.user_id == user_id)
        )
        return result.first()['role'] if result else None
    
    def can_user_edit(self, user_id):
        """Check if user can edit workspace content."""
        role = self.get_user_role(user_id)
        return role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR]
    
    def can_user_manage(self, user_id):
        """Check if user can manage workspace settings."""
        role = self.get_user_role(user_id)
        return role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]

class StandardWorkspace(Base):
    """Association between standards and workspaces."""
    __tablename__ = "standard_workspaces"
    
    id = Column(String(36), primary_key=True)
    standard_id = Column(String(36), ForeignKey('standards.id', ondelete='CASCADE'))
    workspace_id = Column(String(36), ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Track who added it and when
    added_by = Column(String(36), ForeignKey('users.id'))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Custom notes for this standard in this workspace
    notes = Column(Text)
    priority = Column(String(20), default="medium")  # high, medium, low
    
    # Relationships
    standard = relationship("Standard")
    workspace = relationship("Workspace", back_populates="standards")
    added_by_user = relationship("User")

class EvidenceWorkspace(Base):
    """Association between evidence and workspaces."""
    __tablename__ = "evidence_workspaces"
    
    id = Column(String(36), primary_key=True)
    evidence_id = Column(String(36), ForeignKey('evidence.id', ondelete='CASCADE'))
    workspace_id = Column(String(36), ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Track who added it and when
    added_by = Column(String(36), ForeignKey('users.id'))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Review status
    review_status = Column(String(20), default="pending")  # pending, approved, rejected
    reviewed_by = Column(String(36), ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Relationships
    evidence = relationship("Evidence")
    workspace = relationship("Workspace", back_populates="evidence")
    added_by_user = relationship("User", foreign_keys=[added_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])

class WorkspaceInvitation(Base):
    """Pending workspace invitations."""
    __tablename__ = "workspace_invitations"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey('workspaces.id', ondelete='CASCADE'))
    email = Column(String(255), nullable=False)
    role = Column(Enum(WorkspaceRole), nullable=False)
    
    # Invitation details
    invited_by = Column(String(36), ForeignKey('users.id'))
    invitation_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, expired
    accepted_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workspace = relationship("Workspace")
    inviter = relationship("User")