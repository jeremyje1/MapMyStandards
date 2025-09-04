"""
Enterprise feature models for multi-tenancy, RBAC, and audit logging
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
import enum

from ..models.database_schema import Base

# Association table for many-to-many relationship between users and teams
user_teams = Table(
    'user_teams',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('team_id', String, ForeignKey('teams.id'), primary_key=True),
    Column('role', String, nullable=False, default='viewer'),
    Column('joined_at', DateTime, default=datetime.utcnow),
    extend_existing=True  # Allow redefinition if table already exists
)

class UserRole(enum.Enum):
    """User roles within a team"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class Team(Base):
    """Team/Organization model for multi-tenancy"""
    __tablename__ = 'teams'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Team settings
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    
    # Billing
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String)
    subscription_tier: Mapped[str] = mapped_column(String, default='starter')
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Many-to-many with users through association table
    members = relationship("User", secondary=user_teams, back_populates="teams")
    
    # Team's resources
    org_charts = relationship("OrgChart", back_populates="team", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="team", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="team", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="team", cascade="all, delete-orphan")

class TeamInvitation(Base):
    """Invitations to join teams"""
    __tablename__ = 'team_invitations'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey('teams.id'))
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum(UserRole), default=UserRole.VIEWER)
    
    # Invitation details
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    invited_by_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    team = relationship("Team")

class AuditLog(Base):
    """Audit log for tracking all actions"""
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey('teams.id'))
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    
    # Action details
    action: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'create', 'update', 'delete'
    resource_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'org_chart', 'scenario'
    resource_id: Mapped[Optional[str]] = mapped_column(String)
    
    # Change details
    changes: Mapped[Optional[dict]] = mapped_column(JSON)  # before/after values
    ip_address: Mapped[Optional[str]] = mapped_column(String)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="audit_logs")
    user = relationship("User")

class ApiKey(Base):
    """API keys for programmatic access"""
    __tablename__ = 'api_keys'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey('teams.id'))
    
    # Key details
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String, nullable=False)  # First few chars for identification
    
    # Permissions
    scopes: Mapped[List[str]] = mapped_column(JSON, default=['read'])
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)  # requests per hour
    
    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    created_by_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    created_by = relationship("User")
    team = relationship("Team", back_populates="api_keys")

class SessionSecurity(Base):
    """Enhanced session security tracking"""
    __tablename__ = 'session_security'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    
    # Session details
    session_token_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    user_agent: Mapped[str] = mapped_column(Text)
    
    # Security
    two_factor_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_device: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User")

# Feature-specific models that were missing
class OrgChart(Base):
    """Organization chart model"""
    __tablename__ = 'org_charts'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey('teams.id'))
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    chart_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="org_charts")
    user = relationship("User")

class Scenario(Base):
    """Scenario modeling for ROI calculations"""
    __tablename__ = 'scenarios'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey('teams.id'))
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    results: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="scenarios")
    user = relationship("User")

class PowerBIConfig(Base):
    """Power BI configuration for analytics"""
    __tablename__ = 'powerbi_configs'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    workspace_id: Mapped[Optional[str]] = mapped_column(String)
    report_id: Mapped[Optional[str]] = mapped_column(String)
    dataset_id: Mapped[Optional[str]] = mapped_column(String)
    tenant_id: Mapped[Optional[str]] = mapped_column(String)
    client_id: Mapped[Optional[str]] = mapped_column(String)
    embed_token: Mapped[Optional[str]] = mapped_column(Text)
    embed_url: Mapped[Optional[str]] = mapped_column(Text)
    config_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
