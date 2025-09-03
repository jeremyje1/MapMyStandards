"""
Enterprise Dashboard Schemas

Pydantic models for enterprise-level analytics and reporting
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class EnterpriseMetrics(BaseModel):
    """Executive summary metrics for enterprise dashboard"""
    total_teams: int = Field(..., description="Total number of teams")
    active_users: int = Field(..., description="Number of active users in time period")
    compliance_score: float = Field(..., description="Average compliance score across all teams")
    risk_score: str = Field(..., description="Overall risk assessment level")
    teams_growth: float = Field(..., description="Team growth percentage")
    users_growth: float = Field(..., description="User growth percentage")
    compliance_growth: float = Field(..., description="Compliance improvement percentage")
    risk_trend: int = Field(..., description="Change in risk count (negative is improvement)")
    total_activities: int = Field(..., description="Total platform activities in period")
    period_days: int = Field(..., description="Analysis period in days")

class TeamPerformance(BaseModel):
    """Performance metrics for individual teams"""
    name: str = Field(..., description="Team name")
    members: int = Field(..., description="Number of team members")
    org_charts: int = Field(..., description="Number of organizational charts")
    scenarios: int = Field(..., description="Number of compliance scenarios")
    compliance: float = Field(..., description="Team compliance score")
    last_activity: str = Field(..., description="Time since last activity")
    risk_level: str = Field(..., description="Team risk assessment level")

class ActivitySummary(BaseModel):
    """Summary of platform activity"""
    user: str = Field(..., description="User who performed the action")
    action: str = Field(..., description="Action that was performed")
    team: str = Field(..., description="Team context for the action")
    timestamp: str = Field(..., description="Relative time of the action")
    details: Optional[str] = Field(None, description="Additional action details")

class RiskFactor(BaseModel):
    """Individual risk factor assessment"""
    category: str = Field(..., description="Risk category name")
    level: str = Field(..., description="Risk level (Low/Medium/High)")
    score: float = Field(..., description="Numerical risk score")
    description: str = Field(..., description="Risk description")

class TeamRisk(BaseModel):
    """Risk assessment for a team"""
    team: str = Field(..., description="Team name")
    risk_level: str = Field(..., description="Overall risk level")
    score: float = Field(..., description="Numerical risk score")
    factors: List[RiskFactor] = Field(default_factory=list, description="Individual risk factors")

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment across enterprise"""
    overall_risk_level: str = Field(..., description="Enterprise-wide risk level")
    risk_matrix: Dict[str, Dict[str, float]] = Field(..., description="Risk scores by team and category")
    top_risks: List[Dict[str, Any]] = Field(..., description="Highest risk teams")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")

class ComplianceGap(BaseModel):
    """Compliance gap identification"""
    team: str = Field(..., description="Team with compliance gap")
    area: str = Field(..., description="Compliance area with gap")
    severity: str = Field(..., description="Gap severity level")
    description: str = Field(..., description="Description of the gap")
    recommendation: Optional[str] = Field(None, description="Recommended action")

class ComplianceReport(BaseModel):
    """Comprehensive compliance report"""
    overall_compliance: float = Field(..., description="Enterprise average compliance score")
    compliant_teams: int = Field(..., description="Number of compliant teams")
    total_teams: int = Field(..., description="Total number of teams")
    team_scores: List[Dict[str, Any]] = Field(..., description="Individual team compliance scores")
    compliance_gaps: List[ComplianceGap] = Field(..., description="Identified compliance gaps")
    recommendations: List[str] = Field(..., description="Compliance improvement recommendations")

class PerformanceTrend(BaseModel):
    """Performance trend data"""
    period: str = Field(..., description="Time period label")
    value: float = Field(..., description="Metric value for the period")
    change: Optional[float] = Field(None, description="Change from previous period")

class DepartmentAnalytics(BaseModel):
    """Analytics for a specific department"""
    department: str = Field(..., description="Department name")
    teams_count: int = Field(..., description="Number of teams in department")
    avg_compliance: float = Field(..., description="Average compliance score")
    risk_level: str = Field(..., description="Department risk level")
    activity_score: int = Field(..., description="Activity level score")
    trends: List[PerformanceTrend] = Field(default_factory=list, description="Performance trends")

class EnterpriseAnalytics(BaseModel):
    """Comprehensive enterprise analytics"""
    departments: List[DepartmentAnalytics] = Field(..., description="Department-level analytics")
    performance_trends: Dict[str, List[PerformanceTrend]] = Field(..., description="Enterprise-wide trends")
    benchmarks: Dict[str, float] = Field(..., description="Performance benchmarks")
    forecasts: Dict[str, float] = Field(..., description="Projected metrics")

class ExportRequest(BaseModel):
    """Request parameters for data export"""
    format: str = Field(..., description="Export format (csv, xlsx, pdf)")
    date_range: int = Field(30, description="Date range in days")
    include_teams: Optional[List[str]] = Field(None, description="Specific teams to include")
    include_metrics: Optional[List[str]] = Field(None, description="Specific metrics to include")

class ExportResponse(BaseModel):
    """Response for data export request"""
    download_url: str = Field(..., description="URL to download the exported file")
    expires_at: datetime = Field(..., description="When the download link expires")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Export format")

class AlertConfiguration(BaseModel):
    """Configuration for enterprise alerts"""
    metric: str = Field(..., description="Metric to monitor")
    threshold: float = Field(..., description="Alert threshold")
    condition: str = Field(..., description="Alert condition (above/below/equals)")
    notification_method: str = Field(..., description="How to send notifications")
    recipients: List[str] = Field(..., description="Alert recipients")
    enabled: bool = Field(True, description="Whether alert is active")

class AlertInstance(BaseModel):
    """Individual alert instance"""
    id: str = Field(..., description="Alert instance ID")
    configuration: AlertConfiguration = Field(..., description="Alert configuration")
    triggered_at: datetime = Field(..., description="When alert was triggered")
    current_value: float = Field(..., description="Current metric value")
    status: str = Field(..., description="Alert status")
    acknowledged: bool = Field(False, description="Whether alert was acknowledged")

class EnterpriseSettings(BaseModel):
    """Enterprise-level configuration settings"""
    auto_refresh_interval: int = Field(300, description="Dashboard refresh interval in seconds")
    default_time_range: int = Field(30, description="Default time range in days")
    risk_thresholds: Dict[str, float] = Field(..., description="Risk assessment thresholds")
    compliance_targets: Dict[str, float] = Field(..., description="Compliance score targets")
    notification_settings: Dict[str, Any] = Field(..., description="Notification preferences")
    data_retention_days: int = Field(365, description="Data retention period in days")

class DashboardWidget(BaseModel):
    """Configuration for dashboard widgets"""
    id: str = Field(..., description="Widget ID")
    type: str = Field(..., description="Widget type")
    title: str = Field(..., description="Widget title")
    position: Dict[str, int] = Field(..., description="Widget position and size")
    configuration: Dict[str, Any] = Field(..., description="Widget-specific configuration")
    data_source: str = Field(..., description="Data source for the widget")
    refresh_interval: int = Field(60, description="Refresh interval in seconds")

class CustomDashboard(BaseModel):
    """Custom dashboard configuration"""
    id: str = Field(..., description="Dashboard ID")
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    widgets: List[DashboardWidget] = Field(..., description="Dashboard widgets")
    layout: Dict[str, Any] = Field(..., description="Dashboard layout configuration")
    access_level: str = Field(..., description="Who can access this dashboard")
    created_by: str = Field(..., description="Dashboard creator")
    created_at: datetime = Field(..., description="When dashboard was created")
    updated_at: datetime = Field(..., description="When dashboard was last updated")
