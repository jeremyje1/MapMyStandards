"""
Enhanced authentication and authorization service with RBAC
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from fastapi import HTTPException, status
import logging

from ..models.user import User
from ..database.enterprise_models import Team, UserRole, user_teams, ApiKey, SessionSecurity
from .team_service import TeamService

logger = logging.getLogger(__name__)

class EnhancedAuthService:
    """Enhanced authentication service with team-based RBAC"""
    
    @staticmethod
    async def check_team_permission(
        db: AsyncSession,
        user_id: str,
        team_id: str,
        permission: str = "read"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has permission in a team
        Returns (has_permission, user_role)
        """
        role = await TeamService.get_user_role_in_team(db, team_id, user_id)
        
        if not role:
            return (False, None)
        
        has_permission = False
        if permission == "read":
            has_permission = TeamService.can_read(role)
        elif permission == "write":
            has_permission = TeamService.can_write(role)
        elif permission == "manage":
            has_permission = TeamService.can_manage_team(role)
        
        return (has_permission, role)
    
    @staticmethod
    async def require_team_permission(
        db: AsyncSession,
        user_id: str,
        team_id: str,
        permission: str = "read"
    ) -> str:
        """
        Require user to have specific permission in team
        Returns user's role if authorized, raises HTTPException otherwise
        """
        has_permission, role = await EnhancedAuthService.check_team_permission(
            db, user_id, team_id, permission
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return role
    
    @staticmethod
    async def get_or_create_default_team(
        db: AsyncSession,
        user: User
    ) -> Team:
        """Get user's default team or create a personal one"""
        if user.default_team_id:
            team = await db.get(Team, user.default_team_id)
            if team:
                return team
        
        # Create personal team
        team = await TeamService.create_team(
            db=db,
            name=f"{user.name or user.email.split('@')[0]}'s Team",
            owner_id=user.id,
            description="Personal workspace"
        )
        
        return team
    
    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        team_id: str,
        created_by_id: str,
        name: str,
        scopes: List[str] = ["read"],
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, ApiKey]:
        """
        Create an API key for a team
        Returns (plaintext_key, api_key_object)
        """
        # Generate secure key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:8]
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        api_key = ApiKey(
            id=f"apikey_{uuid.uuid4().hex[:12]}",
            team_id=team_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            scopes=scopes,
            expires_at=expires_at,
            created_by_id=created_by_id
        )
        
        db.add(api_key)
        await db.commit()
        
        logger.info(f"API key created for team {team_id} by user {created_by_id}")
        return (f"{prefix}_{raw_key}", api_key)
    
    @staticmethod
    async def verify_api_key(
        db: AsyncSession,
        api_key: str
    ) -> Optional[Tuple[ApiKey, Team]]:
        """Verify an API key and return the key and associated team"""
        try:
            # Extract prefix and validate format
            if "_" not in api_key or len(api_key) < 10:
                return None
            
            prefix = api_key.split("_")[0]
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find API key
            query = select(ApiKey).where(
                and_(
                    ApiKey.prefix == prefix,
                    ApiKey.key_hash == key_hash,
                    ApiKey.active.is_(True)
                )
            )
            
            result = await db.execute(query)
            api_key_obj = result.scalar_one_or_none()
            
            if not api_key_obj:
                return None
            
            # Check expiration
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                return None
            
            # Update last used
            api_key_obj.last_used_at = datetime.utcnow()
            
            # Get team
            team = await db.get(Team, api_key_obj.team_id)
            
            await db.commit()
            
            return (api_key_obj, team)
            
        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            return None
    
    @staticmethod
    async def create_secure_session(
        db: AsyncSession,
        user_id: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        two_factor_verified: bool = False
    ) -> str:
        """Create a secure session with tracking"""
        session_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        session = SessionSecurity(
            id=f"session_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            session_token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            two_factor_verified=two_factor_verified,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(session)
        await db.commit()
        
        logger.info(f"Secure session created for user {user_id}")
        return session_token
    
    @staticmethod
    async def verify_secure_session(
        db: AsyncSession,
        session_token: str,
        ip_address: str
    ) -> Optional[Tuple[SessionSecurity, User]]:
        """Verify a secure session"""
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        query = select(SessionSecurity).where(
            and_(
                SessionSecurity.session_token_hash == token_hash,
                SessionSecurity.expires_at > datetime.utcnow()
            )
        )
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Update activity
        session.last_activity_at = datetime.utcnow()
        
        # Verify IP hasn't changed (optional, can be configured)
        if session.ip_address != ip_address and not session.trusted_device:
            logger.warning(f"Session IP mismatch for user {session.user_id}")
            # Could require re-authentication here
        
        # Get user
        user = await db.get(User, session.user_id)
        
        await db.commit()
        
        return (session, user)
    
    @staticmethod
    async def revoke_api_key(
        db: AsyncSession,
        api_key_id: str
    ) -> bool:
        """Revoke an API key"""
        api_key = await db.get(ApiKey, api_key_id)
        
        if not api_key:
            return False
        
        api_key.active = False
        api_key.revoked_at = datetime.utcnow()
        
        await db.commit()
        logger.info(f"API key {api_key_id} revoked")
        
        return True
    
    @staticmethod
    async def get_team_api_keys(
        db: AsyncSession,
        team_id: str,
        active_only: bool = True
    ) -> List[ApiKey]:
        """Get all API keys for a team"""
        query = select(ApiKey).where(ApiKey.team_id == team_id)
        
        if active_only:
            query = query.where(ApiKey.active.is_(True))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def check_api_key_scope(
        api_key: ApiKey,
        required_scope: str
    ) -> bool:
        """Check if API key has required scope"""
        return required_scope in api_key.scopes or "admin" in api_key.scopes
