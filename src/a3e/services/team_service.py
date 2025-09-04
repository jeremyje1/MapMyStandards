"""
Team management service for enterprise features
Handles team creation, member management, and permissions
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.orm import selectinload
import hashlib

from ..database.enterprise_models import Team, TeamInvitation, UserRole, user_teams
from ..models.user import User
from ..core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class TeamService:
    """Service for managing teams and team members"""
    
    @staticmethod
    async def create_team(
        db: AsyncSession,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Team:
        """Create a new team with the user as owner"""
        try:
            # Generate unique slug
            base_slug = name.lower().replace(' ', '-').replace('_', '-')
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            
            # Create team
            team = Team(
                id=f"team_{uuid.uuid4().hex[:12]}",
                name=name,
                slug=slug,
                description=description,
                settings=settings or {},
                created_by_id=owner_id
            )
            
            db.add(team)
            await db.flush()
            
            # Add owner to team
            await db.execute(
                user_teams.insert().values(
                    user_id=owner_id,
                    team_id=team.id,
                    role=UserRole.OWNER.value,
                    joined_at=datetime.utcnow()
                )
            )
            
            # Update user's default team
            await db.execute(
                update(User)
                .where(User.id == owner_id)
                .values(default_team_id=team.id)
            )
            
            await db.commit()
            logger.info(f"Team {team.id} created by user {owner_id}")
            return team
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating team: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_teams(
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all teams for a user with their role"""
        query = (
            select(Team, user_teams.c.role)
            .join(user_teams)
            .where(user_teams.c.user_id == user_id)
            .order_by(Team.created_at.desc())
        )
        
        result = await db.execute(query)
        teams = []
        for team, role in result:
            teams.append({
                "team": team,
                "role": role
            })
        
        return teams
    
    @staticmethod
    async def get_team_members(
        db: AsyncSession,
        team_id: str
    ) -> List[Dict[str, Any]]:
        """Get all members of a team with their roles"""
        query = (
            select(User, user_teams.c.role, user_teams.c.joined_at)
            .join(user_teams)
            .where(user_teams.c.team_id == team_id)
            .order_by(user_teams.c.joined_at)
        )
        
        result = await db.execute(query)
        members = []
        for user, role, joined_at in result:
            members.append({
                "user": user,
                "role": role,
                "joined_at": joined_at
            })
        
        return members
    
    @staticmethod
    async def invite_member(
        db: AsyncSession,
        team_id: str,
        email: str,
        role: UserRole,
        invited_by_id: str
    ) -> TeamInvitation:
        """Create an invitation for a new team member"""
        # Generate secure token
        token = secrets.urlsafe()
        
        invitation = TeamInvitation(
            id=f"invite_{uuid.uuid4().hex[:12]}",
            team_id=team_id,
            email=email,
            role=role,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=7),
            invited_by_id=invited_by_id
        )
        
        db.add(invitation)
        await db.commit()
        
        logger.info(f"Invitation created for {email} to join team {team_id}")
        return invitation
    
    @staticmethod
    async def accept_invitation(
        db: AsyncSession,
        token: str,
        user_id: str
    ) -> Optional[Team]:
        """Accept a team invitation"""
        # Find invitation
        query = select(TeamInvitation).where(
            and_(
                TeamInvitation.token == token,
                TeamInvitation.accepted.is_(False),
                TeamInvitation.expires_at > datetime.utcnow()
            )
        )
        
        result = await db.execute(query)
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            return None
        
        # Add user to team
        await db.execute(
            user_teams.insert().values(
                user_id=user_id,
                team_id=invitation.team_id,
                role=invitation.role.value,
                joined_at=datetime.utcnow()
            )
        )
        
        # Mark invitation as accepted
        invitation.accepted = True
        invitation.accepted_at = datetime.utcnow()
        
        # Get team
        team = await db.get(Team, invitation.team_id)
        
        await db.commit()
        logger.info(f"User {user_id} joined team {invitation.team_id}")
        
        return team
    
    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        team_id: str,
        user_id: str,
        new_role: UserRole
    ) -> bool:
        """Update a team member's role"""
        await db.execute(
            update(user_teams)
            .where(
                and_(
                    user_teams.c.team_id == team_id,
                    user_teams.c.user_id == user_id
                )
            )
            .values(role=new_role.value)
        )
        
        await db.commit()
        logger.info(f"Updated user {user_id} role to {new_role.value} in team {team_id}")
        return True
    
    @staticmethod
    async def remove_member(
        db: AsyncSession,
        team_id: str,
        user_id: str
    ) -> bool:
        """Remove a member from a team"""
        await db.execute(
            delete(user_teams)
            .where(
                and_(
                    user_teams.c.team_id == team_id,
                    user_teams.c.user_id == user_id
                )
            )
        )
        
        await db.commit()
        logger.info(f"Removed user {user_id} from team {team_id}")
        return True
    
    @staticmethod
    async def get_user_role_in_team(
        db: AsyncSession,
        team_id: str,
        user_id: str
    ) -> Optional[str]:
        """Get a user's role in a specific team"""
        query = select(user_teams.c.role).where(
            and_(
                user_teams.c.team_id == team_id,
                user_teams.c.user_id == user_id
            )
        )
        
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        
        return role
    
    @staticmethod
    def can_manage_team(role: str) -> bool:
        """Check if a role can manage team settings and members"""
        return role in [UserRole.OWNER.value, UserRole.ADMIN.value]
    
    @staticmethod
    def can_write(role: str) -> bool:
        """Check if a role can create/edit content"""
        return role in [UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.MANAGER.value]
    
    @staticmethod
    def can_read(role: str) -> bool:
        """Check if a role can view content"""
        # All roles can read
        return True
