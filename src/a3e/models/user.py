"""
User and authentication models for A3E platform - SQLite Compatible
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Optional
import os

from . import Base

class User(Base):
    """User account model"""
    __tablename__ = 'users'
    
    # Use String(36) for UUIDs to ensure SQLite compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    # Organization info
    institution_name = Column(String(255))
    institution_type = Column(String(50))  # college, multi_campus, system, etc.
    role = Column(String(100))  # e.g., "Accreditation Director"
    primary_accreditor = Column(String(255))  # e.g., "WASC", "HLC", "MSCHE"
    department = Column(String(255))  # e.g., "Academic Affairs"
    
    # Trial and subscription info
    is_trial = Column(Boolean, default=True)
    trial_started_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(DateTime)
    subscription_tier = Column(String(50))  # essential, professional, enterprise
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True)
    
    # API access
    api_key = Column(String(255), unique=True, index=True)
    api_key_created_at = Column(DateTime)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    last_login = Column(DateTime)  # Alias for compatibility
    
    # Auth tokens
    refresh_token = Column(String(500))
    refresh_token_expires = Column(DateTime)
    reset_token = Column(String(255))
    reset_token_expires = Column(DateTime)
    
    # Contact info
    phone = Column(String(50))
    newsletter_opt_in = Column(Boolean, default=False)
    
    # Usage tracking
    documents_analyzed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    compliance_checks_run = Column(Integer, default=0)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)
    onboarding_data = Column(JSON)  # Store full onboarding wizard responses (step data, goals, etc.)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="user", cascade="all, delete-orphan")
    # Note: workspaces relationship defined in workspace.py to avoid circular import
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', institution='{self.institution_name}')>"
    
    @property
    def is_trial_active(self) -> bool:
        """Check if user is in active trial period"""
        if not self.is_trial or not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at
    
    @property
    def days_remaining_in_trial(self) -> int:
        """Get days remaining in trial"""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)


class UserSession(Base):
    """User session tracking for JWT tokens"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        if not self.is_active or self.revoked_at:
            return False
        return datetime.utcnow() < self.expires_at


class PasswordReset(Base):
    """Password reset token tracking"""
    __tablename__ = 'password_resets'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    reset_token = Column(String(255), unique=True, nullable=False, index=True)
    reset_code = Column(String(10))  # For 6-character verification codes
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="password_resets")
    
    @property
    def is_valid(self) -> bool:
        """Check if reset token is still valid"""
        if self.used_at:
            return False
        return datetime.utcnow() < self.expires_at


class UsageEvent(Base):
    """Track user activity and feature usage"""
    __tablename__ = 'usage_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    event_type = Column(String(50), nullable=False)  # document_upload, report_generation, etc.
    event_data = Column(JSON)  # Additional event-specific data
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="usage_events")
    
    def __repr__(self):
        return f"<UsageEvent(id='{self.id}', type='{self.event_type}', user='{self.user_id}')>"
