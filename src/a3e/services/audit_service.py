"""
Audit logging service for tracking user actions
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import logging

from ..database.enterprise_models import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """Service for audit logging and compliance tracking"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_type: str,
        team_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a user action for audit trail"""
        try:
            audit_log = AuditLog(
                id=f"audit_{uuid.uuid4().hex[:12]}",
                team_id=team_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info(f"Audit log created: {action} on {resource_type} by user {user_id}")
            return audit_log
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating audit log: {str(e)}")
            raise
    
    @staticmethod
    async def get_team_audit_logs(
        db: AsyncSession,
        team_id: str,
        limit: int = 100,
        offset: int = 0,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[AuditLog]:
        """Get audit logs for a team with filtering"""
        query = select(AuditLog).where(AuditLog.team_id == team_id)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        query = query.order_by(desc(AuditLog.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_audit_logs(
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get all audit logs for a specific user"""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def format_change_description(
        action: str,
        resource_type: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a human-readable description of changes"""
        descriptions = {
            "create": f"Created {resource_type}",
            "update": f"Updated {resource_type}",
            "delete": f"Deleted {resource_type}",
            "view": f"Viewed {resource_type}",
            "export": f"Exported {resource_type}",
            "share": f"Shared {resource_type}",
            "invite": f"Invited user to {resource_type}",
            "login": "Logged in",
            "logout": "Logged out"
        }
        
        base_description = descriptions.get(action, f"{action} {resource_type}")
        
        if changes and action == "update":
            changed_fields = list(changes.keys())
            if len(changed_fields) == 1:
                base_description += f" ({changed_fields[0]})"
            elif len(changed_fields) > 1:
                base_description += f" ({len(changed_fields)} fields)"
        
        return base_description
    
    @staticmethod
    async def get_resource_history(
        db: AsyncSession,
        resource_type: str,
        resource_id: str,
        team_id: Optional[str] = None
    ) -> List[AuditLog]:
        """Get complete history for a specific resource"""
        query = select(AuditLog).where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        )
        
        if team_id:
            query = query.where(AuditLog.team_id == team_id)
        
        query = query.order_by(desc(AuditLog.created_at))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_activity_summary(
        db: AsyncSession,
        team_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get activity summary for a team over the specified days"""
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.team_id == team_id,
                AuditLog.created_at >= since
            )
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Aggregate by action and resource type
        summary = {
            "total_actions": len(logs),
            "unique_users": len(set(log.user_id for log in logs)),
            "actions_by_type": {},
            "resources_by_type": {}
        }
        
        for log in logs:
            # Count actions
            if log.action not in summary["actions_by_type"]:
                summary["actions_by_type"][log.action] = 0
            summary["actions_by_type"][log.action] += 1
            
            # Count resources
            if log.resource_type not in summary["resources_by_type"]:
                summary["resources_by_type"][log.resource_type] = 0
            summary["resources_by_type"][log.resource_type] += 1
        
        return summary
