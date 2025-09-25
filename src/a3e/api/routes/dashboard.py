"""
Dashboard data endpoints for A3E platform
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ...models.user import User, UsageEvent
from ...services.database_service import DatabaseService
from ...core.config import get_settings
from ..routes.auth_impl import verify_jwt_token_email as verify_jwt_token

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
# Require Authorization header for real user data
security = HTTPBearer(auto_error=True)
settings = get_settings()
logger = logging.getLogger(__name__)

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Auth dependency
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user (no demo fallbacks)."""
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")

    # Standard JWT verification path
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Check trial status
    if user.is_trial and not user.is_trial_active:
        raise HTTPException(status_code=403, detail="Trial period has expired")

    return user


@router.get("/overview")
async def get_dashboard_overview(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get dashboard overview data"""
    try:
        # Calculate key metrics
        compliance_score = calculate_compliance_score(current_user)
        time_saved = calculate_time_saved(current_user)
        money_saved = calculate_money_saved(current_user)

        # Get recent activity
        stmt = select(UsageEvent).where(
            UsageEvent.user_id == current_user.get("id")
        ).order_by(UsageEvent.created_at.desc()).limit(10)

        result = await db.execute(stmt)
        recent_events = result.scalars().all()
        
        recent_activity = []
        for event in recent_events:
            details = event.event_data or {}
            recent_activity.append(
                {
                    "type": event.event_type,
                    "category": (details.get("category") if isinstance(details, dict) else None),
                    "timestamp": event.created_at.isoformat() if event.created_at else None,
                    "details": details,
                }
            )
        
        return {
            "user": {
                "name": current_user.name,
                "email": current_user.get("email"),
                "institution": current_user.institution_name,
                "role": current_user.get("role"),
                "subscription_tier": current_user.subscription_tier,
                "is_trial": current_user.is_trial,
                "trial_days_remaining": current_user.days_remaining_in_trial if current_user.is_trial else None
            },
            "metrics": {
                "documents_analyzed": current_user.documents_analyzed,
                "reports_generated": current_user.reports_generated,
                "compliance_checks": current_user.compliance_checks_run,
                "compliance_score": compliance_score,
                "time_saved_hours": time_saved,
                "money_saved_usd": money_saved
            },
            "quick_stats": {
                "active_standards": 0,
                "mapped_evidence": 0,
                "gaps_identified": 0,
                "recommendations": 0
            },
            "note": "Metrics will populate after you upload documents and processing completes.",
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/analytics")
async def get_analytics_data(
    period: str = "week",  # week, month, quarter
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics data for charts and graphs"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get usage trends
        stmt = select(
            func.date(UsageEvent.created_at).label('date'),
            func.count(UsageEvent.id).label('count'),
            UsageEvent.event_type.label('event_type')
        ).where(
            UsageEvent.user_id == current_user.get("id"),
            UsageEvent.created_at >= start_date
        ).group_by(
            func.date(UsageEvent.created_at),
            UsageEvent.event_type
        )
        
        result = await db.execute(stmt)
        usage_data = result.all()
        
        # Format usage trends
        usage_trends = {}
        for row in usage_data:
            date_str = row.date.isoformat() if row.date else "unknown"
            if date_str not in usage_trends:
                usage_trends[date_str] = {}
            # group by event_type to avoid reliance on JSON fields
            usage_trends[date_str][getattr(row, 'event_type', None) or "other"] = row.count

        # Placeholder until real trend computation is implemented
        compliance_trends: List[Dict[str, Any]] = []

        return {
            "period": period,
            "usage_trends": usage_trends,
            "compliance_trends": compliance_trends,
            "top_standards": [],
            "improvement_areas": [],
            "note": "Analytics will populate after you upload documents and the system processes activity."
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analytics data"
        )


@router.get("/notifications")
async def get_notifications(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user notifications and alerts"""
    try:
        notifications = []
        
        # Trial expiration warning
        if current_user.is_trial:
            days_left = current_user.days_remaining_in_trial
            if days_left <= 3:
                notifications.append({
                    "id": "trial_expiring",
                    "type": "warning",
                    "title": f"Trial Expires in {days_left} Days",
                    "message": "Upgrade now to keep your data and continue using A³E",
                    "action": {
                        "label": "Upgrade Now",
                        "url": "/pricing"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Mock notifications for demonstration
        notifications.extend([
            {
                "id": "new_standards",
                "type": "info",
                "title": "New HLC Standards Available",
                "message": "Updated 2025 standards have been added to your library",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "report_ready",
                "type": "success",
                "title": "Gap Analysis Report Ready",
                "message": "Your comprehensive gap analysis report is ready for download",
                "action": {
                    "label": "View Report",
                    "url": "/reports/latest"
                },
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat()
            }
        ])
        
        return {
            "notifications": notifications,
            "unread_count": len([n for n in notifications if n.get("type") in ["warning", "error"]])
        }
        
    except Exception as e:
        logger.error(f"Notifications error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve notifications"
        )


# Helper functions
def calculate_compliance_score(user: User) -> int:
    """Calculate overall compliance score"""
    # Mock calculation based on user activity
    base_score = 70
    doc_bonus = min(user.documents_analyzed * 2, 20)
    report_bonus = min(user.reports_generated * 3, 10)
    return min(base_score + doc_bonus + report_bonus, 100)


def calculate_time_saved(user: User) -> int:
    """Calculate hours saved through automation"""
    # Estimate: 3 hours saved per document, 5 hours per report
    return (user.documents_analyzed * 3) + (user.reports_generated * 5)


def calculate_money_saved(user: User) -> int:
    """Calculate money saved vs manual processing"""
    # Estimate: $150/hour for consultant work
    hours_saved = calculate_time_saved(user)
    return hours_saved * 150


def generate_compliance_trends(period: str) -> List[Dict[str, Any]]:
    """Generate mock compliance trend data"""
    import random
    
    days = 7 if period == "week" else 30 if period == "month" else 90
    trends = []
    base_score = 75
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days-i-1)
        score = base_score + random.randint(-5, 10) + (i // 10)  # Gradual improvement
        score = min(max(score, 60), 95)  # Keep between 60-95
        
        trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "score": score,
            "documents": random.randint(1, 5)
        })
    
    return trends
