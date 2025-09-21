"""
Enterprise Dashboard API Routes

Provides comprehensive analytics and metrics for enterprise-level monitoring:
- Cross-team performance analytics
- Compliance risk assessment
- Activity tracking and reporting
- Executive summary dashboards
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, List, Dict, Any, Optional
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

from ...database.connection import db_manager
from ...models.user import User
from ...database.enterprise_models import OrgChart, Scenario
from ...database.enterprise_models import Team, TeamInvitation, AuditLog
from ..dependencies import get_current_user
from ...schemas.enterprise import (
    EnterpriseMetrics,
    TeamPerformance,
    ActivitySummary,
    RiskAssessment,
    ComplianceReport
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])

# Dependency for async database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        yield session

@router.get("/metrics", response_model=EnterpriseMetrics)
async def get_enterprise_metrics(
    time_range: int = 30,  # days
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive enterprise metrics including:
    - Total teams and active users
    - Overall compliance scores
    - Risk assessments
    - Growth trends
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range)
        
        # Check if user has enterprise access
        if not _has_enterprise_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise dashboard access required"
            )
        
        # Get total teams
        total_teams = db.query(Team).count()
        
        # Get active users (users who logged in within time range)
        active_users = db.query(User).filter(
            User.last_login >= start_date
        ).count()
        
        # Calculate compliance score (average across all teams)
        compliance_scores = db.query(
            func.avg(Team.compliance_score).label('avg_compliance')
        ).first()
        
        avg_compliance = compliance_scores.avg_compliance or 0
        
        # Calculate growth metrics (compare with previous period)
        prev_start = start_date - timedelta(days=time_range)
        
        prev_teams = db.query(Team).filter(
            Team.created_at < start_date,
            Team.created_at >= prev_start
        ).count()
        
        prev_active_users = db.query(User).filter(
            User.last_login >= prev_start,
            User.last_login < start_date
        ).count()
        
        # Calculate growth percentages
        teams_growth = _calculate_growth(total_teams - prev_teams, prev_teams)
        users_growth = _calculate_growth(active_users - prev_active_users, prev_active_users)
        
        # Risk assessment (simplified)
        risk_score = _calculate_risk_score(db, avg_compliance)
        
        # Activity count for the period
        total_activities = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date
        ).count()
        
        return EnterpriseMetrics(
            total_teams=total_teams,
            active_users=active_users,
            compliance_score=round(avg_compliance, 1),
            risk_score=risk_score,
            teams_growth=teams_growth,
            users_growth=users_growth,
            compliance_growth=2.5,  # Mock value - would calculate from historical data
            risk_trend=-1,  # Mock value - would calculate risk change
            total_activities=total_activities,
            period_days=time_range
        )
        
    except Exception as e:
        logger.error(f"Failed to get enterprise metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enterprise metrics"
        )

@router.get("/teams/performance", response_model=List[TeamPerformance])
async def get_team_performance(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed performance metrics for all teams
    """
    try:
        if not _has_enterprise_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise dashboard access required"
            )
        
        teams = db.query(Team).all()
        performance_data = []
        
        for team in teams:
            # Count team members
            member_count = db.query(TeamInvitation).filter(
                TeamInvitation.team_id == team.id
            ).count()
            
            # Count org charts
            org_chart_count = db.query(OrgChart).filter(
                OrgChart.team_id == team.id
            ).count()
            
            # Count scenarios
            scenario_count = db.query(Scenario).filter(
                Scenario.team_id == team.id
            ).count()
            
            # Get last activity
            last_activity = db.query(AuditLog).filter(
                AuditLog.team_id == team.id
            ).order_by(desc(AuditLog.timestamp)).first()
            
            last_activity_str = "No activity"
            if last_activity:
                time_diff = datetime.utcnow() - last_activity.timestamp
                if time_diff.days > 0:
                    last_activity_str = f"{time_diff.days} days ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    last_activity_str = f"{hours} hours ago"
                else:
                    minutes = time_diff.seconds // 60
                    last_activity_str = f"{minutes} minutes ago"
            
            # Calculate risk level based on compliance and activity
            risk_level = _calculate_team_risk_level(
                team.compliance_score or 0,
                last_activity.timestamp if last_activity else None
            )
            
            performance_data.append(TeamPerformance(
                name=team.name,
                members=member_count,
                org_charts=org_chart_count,
                scenarios=scenario_count,
                compliance=round(team.compliance_score or 0, 1),
                last_activity=last_activity_str,
                risk_level=risk_level
            ))
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get team performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team performance data"
        )

@router.get("/activity/recent", response_model=List[ActivitySummary])
async def get_recent_activity(
    limit: int = 20,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get recent platform activity across all teams
    """
    try:
        if not _has_enterprise_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise dashboard access required"
            )
        
        # Get recent audit logs with user and team information
        recent_logs = db.query(AuditLog)\
            .join(User, AuditLog.user_id == User.id)\
            .join(Team, AuditLog.team_id == Team.id, isouter=True)\
            .order_by(desc(AuditLog.timestamp))\
            .limit(limit)\
            .all()
        
        activities = []
        for log in recent_logs:
            user = db.query(User).filter(User.id == log.user_id).first()
            team = db.query(Team).filter(Team.id == log.team_id).first() if log.team_id else None
            
            time_diff = datetime.utcnow() - log.timestamp
            if time_diff.days > 0:
                timestamp_str = f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                timestamp_str = f"{hours} hours ago"
            else:
                minutes = time_diff.seconds // 60
                timestamp_str = f"{minutes} minutes ago"
            
            activities.append(ActivitySummary(
                user=user.full_name if user else "Unknown User",
                action=log.action,
                team=team.name if team else "System",
                timestamp=timestamp_str,
                details=log.details
            ))
        
        return activities
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activity"
        )

@router.get("/risk/assessment", response_model=RiskAssessment)
async def get_risk_assessment(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive risk assessment across all teams and departments
    """
    try:
        if not _has_enterprise_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise dashboard access required"
            )
        
        # Risk categories and their weights
        risk_categories = {
            "Data Security": 0.25,
            "Compliance": 0.30,
            "Process": 0.20,
            "Training": 0.15,
            "Documentation": 0.10
        }
        
        # Get all teams
        teams = db.query(Team).all()
        
        # Calculate risk scores for each team and category
        risk_matrix = {}
        overall_risks = []
        
        for team in teams:
            team_risks = {}
            for category, weight in risk_categories.items():
                # Mock risk calculation - in production would use actual metrics
                risk_score = _calculate_category_risk(db, team.id, category)
                team_risks[category] = risk_score
            
            risk_matrix[team.name] = team_risks
            
            # Calculate overall team risk
            weighted_risk = sum(
                score * risk_categories[category] 
                for category, score in team_risks.items()
            )
            
            if weighted_risk > 2.5:
                risk_level = "High"
            elif weighted_risk > 1.5:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            overall_risks.append({
                "team": team.name,
                "risk_level": risk_level,
                "score": round(weighted_risk, 2)
            })
        
        # Identify top risks
        top_risks = sorted(overall_risks, key=lambda x: x["score"], reverse=True)[:5]
        
        return RiskAssessment(
            overall_risk_level=_calculate_overall_risk_level(overall_risks),
            risk_matrix=risk_matrix,
            top_risks=top_risks,
            recommendations=_generate_risk_recommendations(top_risks)
        )
        
    except Exception as e:
        logger.error(f"Failed to get risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk assessment"
        )

@router.get("/compliance/report", response_model=ComplianceReport)
async def get_compliance_report(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate comprehensive compliance report for enterprise oversight
    """
    try:
        if not _has_enterprise_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise dashboard access required"
            )
        
        # Get all teams with compliance data
        teams = db.query(Team).all()
        
        compliance_scores = []
        gaps = []
        
        for team in teams:
            compliance_score = team.compliance_score or 0
            compliance_scores.append({
                "team": team.name,
                "score": compliance_score,
                "status": "Compliant" if compliance_score >= 80 else "At Risk" if compliance_score >= 60 else "Non-Compliant"
            })
            
            # Identify compliance gaps (mock data)
            if compliance_score < 80:
                gaps.append({
                    "team": team.name,
                    "area": "Documentation",
                    "severity": "High" if compliance_score < 60 else "Medium",
                    "description": f"Compliance score below threshold: {compliance_score}%"
                })
        
        # Calculate overall metrics
        avg_compliance = sum(team.compliance_score or 0 for team in teams) / len(teams) if teams else 0
        compliant_teams = len([s for s in compliance_scores if s["score"] >= 80])
        
        return ComplianceReport(
            overall_compliance=round(avg_compliance, 1),
            compliant_teams=compliant_teams,
            total_teams=len(teams),
            team_scores=compliance_scores,
            compliance_gaps=gaps,
            recommendations=_generate_compliance_recommendations(gaps)
        )
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )

# Helper functions

def _has_enterprise_access(user: User) -> bool:
    """Check if user has enterprise dashboard access"""
    # In production, implement proper role-based access control
    return user.role in ["owner", "admin"]

def _calculate_growth(current: int, previous: int) -> float:
    """Calculate growth percentage"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current / previous) * 100, 1)

def _calculate_risk_score(db: AsyncSession, compliance_score: float) -> str:
    """Calculate overall risk score based on various factors"""
    if compliance_score >= 85:
        return "Low"
    elif compliance_score >= 70:
        return "Medium"
    else:
        return "High"

def _calculate_team_risk_level(compliance_score: float, last_activity: Optional[datetime]) -> str:
    """Calculate risk level for a specific team"""
    risk_factors = 0
    
    if compliance_score < 80:
        risk_factors += 1
    if compliance_score < 60:
        risk_factors += 1
    
    if last_activity:
        days_since_activity = (datetime.utcnow() - last_activity).days
        if days_since_activity > 7:
            risk_factors += 1
        if days_since_activity > 30:
            risk_factors += 1
    else:
        risk_factors += 2
    
    if risk_factors >= 3:
        return "High"
    elif risk_factors >= 1:
        return "Medium"
    else:
        return "Low"

def _calculate_category_risk(db: AsyncSession, team_id: int, category: str) -> float:
    """Calculate risk score for a specific category (mock implementation)"""
    # Mock implementation - in production would analyze actual data
    import random
    random.seed(team_id + hash(category))
    return round(random.uniform(0, 3), 1)

def _calculate_overall_risk_level(risks: List[Dict]) -> str:
    """Calculate overall enterprise risk level"""
    high_risk_teams = len([r for r in risks if r["risk_level"] == "High"])
    total_teams = len(risks)
    
    if high_risk_teams / total_teams > 0.3:
        return "High"
    elif high_risk_teams / total_teams > 0.1:
        return "Medium"
    else:
        return "Low"

def _generate_risk_recommendations(top_risks: List[Dict]) -> List[str]:
    """Generate risk mitigation recommendations"""
    recommendations = []
    
    for risk in top_risks[:3]:  # Top 3 risks
        if risk["score"] > 2.5:
            recommendations.append(f"Immediate attention required for {risk['team']} - implement enhanced monitoring")
        elif risk["score"] > 1.5:
            recommendations.append(f"Schedule compliance review for {risk['team']} within 30 days")
    
    if len(recommendations) == 0:
        recommendations.append("All teams operating within acceptable risk parameters")
    
    return recommendations

def _generate_compliance_recommendations(gaps: List[Dict]) -> List[str]:
    """Generate compliance improvement recommendations"""
    recommendations = []
    
    high_severity_gaps = [g for g in gaps if g["severity"] == "High"]
    if high_severity_gaps:
        recommendations.append("Address high-severity compliance gaps immediately")
        recommendations.append("Implement mandatory compliance training for affected teams")
    
    medium_severity_gaps = [g for g in gaps if g["severity"] == "Medium"]
    if medium_severity_gaps:
        recommendations.append("Schedule compliance reviews for teams with medium-severity gaps")
    
    if not gaps:
        recommendations.append("All teams meeting compliance requirements")
        recommendations.append("Consider implementing advanced compliance automation")
    
    return recommendations
