"""
Real-time Analytics Service
Handles real-time data streaming, custom visualizations, and advanced analytics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import websockets
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from sqlalchemy import func, and_, or_

from ..models.user import User
from ..database.enterprise_models import OrgChart, Scenario, PowerBIConfig
from ..database.connection import db_manager

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """Real-time analytics event"""
    event_type: str
    user_id: str
    institution_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    metric_name: str
    metric_value: float


@dataclass
class RealTimeMetric:
    """Real-time metric with streaming data"""
    name: str
    value: float
    trend: str  # 'up', 'down', 'stable'
    change_percent: float
    updated_at: datetime
    category: str


@dataclass
class DashboardTemplate:
    """Advanced dashboard template configuration"""
    id: str
    name: str
    description: str
    target_audience: str  # 'administrator', 'faculty', 'executive'
    institution_type: str  # 'university', 'community_college', 'k12'
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    filters: List[Dict[str, Any]]
    permissions: Dict[str, List[str]]


class RealTimeAnalyticsService:
    """
    Advanced analytics service with real-time capabilities
    Provides streaming data, custom visualizations, and dynamic dashboards
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.metrics_cache: Dict[str, RealTimeMetric] = {}
        self.dashboard_templates: Dict[str, DashboardTemplate] = {}
        self._initialize_templates()
        
    def _initialize_templates(self):
        """Initialize pre-built dashboard templates"""
        self.dashboard_templates = {
            "executive_summary": DashboardTemplate(
                id="executive_summary",
                name="Executive Summary Dashboard",
                description="High-level compliance metrics for leadership",
                target_audience="executive",
                institution_type="university",
                layout={
                    "type": "grid",
                    "columns": 12,
                    "rows": 8,
                    "responsive": True
                },
                widgets=[
                    {
                        "id": "compliance_score",
                        "type": "kpi_card",
                        "title": "Overall Compliance Score",
                        "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                        "config": {
                            "metric": "compliance_score",
                            "format": "percentage",
                            "target": 85,
                            "color_scheme": "red_yellow_green"
                        }
                    },
                    {
                        "id": "standards_progress",
                        "type": "progress_chart",
                        "title": "Standards Implementation Progress",
                        "position": {"x": 3, "y": 0, "w": 6, "h": 4},
                        "config": {
                            "chart_type": "donut",
                            "metric": "standards_completion",
                            "breakdown": "by_category"
                        }
                    },
                    {
                        "id": "risk_indicators",
                        "type": "risk_matrix",
                        "title": "Risk Assessment",
                        "position": {"x": 9, "y": 0, "w": 3, "h": 4},
                        "config": {
                            "risk_categories": ["high", "medium", "low"],
                            "impact_vs_probability": True
                        }
                    }
                ],
                filters=[
                    {
                        "id": "time_period",
                        "type": "date_range",
                        "default": "last_30_days"
                    },
                    {
                        "id": "department",
                        "type": "multi_select",
                        "source": "departments"
                    }
                ],
                permissions={
                    "view": ["executive", "administrator"],
                    "edit": ["administrator"],
                    "export": ["executive", "administrator"]
                }
            ),
            "faculty_dashboard": DashboardTemplate(
                id="faculty_dashboard",
                name="Faculty Compliance Dashboard",
                description="Detailed compliance tracking for faculty and staff",
                target_audience="faculty",
                institution_type="university",
                layout={
                    "type": "tabs",
                    "tabs": ["overview", "my_tasks", "department", "resources"]
                },
                widgets=[
                    {
                        "id": "my_compliance_status",
                        "type": "personal_scorecard",
                        "title": "My Compliance Status",
                        "tab": "overview",
                        "config": {
                            "include_training": True,
                            "include_certifications": True,
                            "include_deadlines": True
                        }
                    },
                    {
                        "id": "pending_actions",
                        "type": "task_list",
                        "title": "Pending Actions",
                        "tab": "my_tasks",
                        "config": {
                            "sort": "priority",
                            "group_by": "category",
                            "show_deadlines": True
                        }
                    }
                ],
                filters=[
                    {
                        "id": "my_department",
                        "type": "single_select",
                        "source": "user_department",
                        "locked": True
                    }
                ],
                permissions={
                    "view": ["faculty", "staff", "administrator"],
                    "edit": ["administrator"],
                    "export": ["faculty", "staff", "administrator"]
                }
            ),
            "operational_dashboard": DashboardTemplate(
                id="operational_dashboard",
                name="Operational Analytics Dashboard",
                description="Detailed operational metrics and trends",
                target_audience="administrator",
                institution_type="university",
                layout={
                    "type": "grid",
                    "columns": 16,
                    "rows": 12,
                    "responsive": True
                },
                widgets=[
                    {
                        "id": "real_time_metrics",
                        "type": "metrics_stream",
                        "title": "Real-Time Metrics",
                        "position": {"x": 0, "y": 0, "w": 8, "h": 3},
                        "config": {
                            "metrics": ["active_users", "document_uploads", "compliance_checks"],
                            "update_interval": 5000,
                            "show_trends": True
                        }
                    },
                    {
                        "id": "system_health",
                        "type": "health_monitor",
                        "title": "System Health",
                        "position": {"x": 8, "y": 0, "w": 4, "h": 3},
                        "config": {
                            "show_api_status": True,
                            "show_database_status": True,
                            "show_powerbi_status": True
                        }
                    }
                ],
                filters=[
                    {
                        "id": "time_granularity",
                        "type": "single_select",
                        "options": ["minute", "hour", "day"],
                        "default": "hour"
                    }
                ],
                permissions={
                    "view": ["administrator"],
                    "edit": ["administrator"],
                    "export": ["administrator"]
                }
            )
        }
    
    async def register_connection(self, websocket: WebSocket, user_id: str):
        """Register a new WebSocket connection for real-time updates"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected for real-time updates")
        
        # Send initial metrics
        await self.send_initial_metrics(websocket, user_id)
    
    async def unregister_connection(self, user_id: str):
        """Unregister a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from real-time updates")
    
    async def send_initial_metrics(self, websocket: WebSocket, user_id: str):
        """Send initial metrics to a newly connected user"""
        try:
            initial_data = {
                "type": "initial_metrics",
                "data": {
                    "compliance_score": await self.get_compliance_score(user_id),
                    "active_standards": await self.get_active_standards_count(user_id),
                    "pending_actions": await self.get_pending_actions_count(user_id),
                    "recent_activity": await self.get_recent_activity(user_id)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(initial_data))
        except Exception as e:
            logger.error(f"Failed to send initial metrics to {user_id}: {str(e)}")
    
    async def broadcast_metric_update(self, metric: RealTimeMetric, user_ids: Optional[List[str]] = None):
        """Broadcast a metric update to connected users"""
        message = {
            "type": "metric_update",
            "data": asdict(metric),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        target_users = user_ids or list(self.active_connections.keys())
        
        for user_id in target_users:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send update to {user_id}: {str(e)}")
                    # Remove disconnected connection
                    await self.unregister_connection(user_id)
    
    async def track_event(self, event: AnalyticsEvent):
        """Track an analytics event and trigger real-time updates"""
        try:
            # Process the event
            await self._process_event(event)
            
            # Update relevant metrics
            updated_metrics = await self._calculate_metrics_from_event(event)
            
            # Broadcast updates
            for metric in updated_metrics:
                await self.broadcast_metric_update(metric, [event.user_id])
                
        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}")
    
    async def _process_event(self, event: AnalyticsEvent):
        """Process an analytics event"""
        # Store event (in production, you'd store to database or event store)
        logger.info(f"Processing event: {event.event_type} for user {event.user_id}")
        
        # Trigger event handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed: {str(e)}")
    
    async def _calculate_metrics_from_event(self, event: AnalyticsEvent) -> List[RealTimeMetric]:
        """Calculate metrics based on an event"""
        metrics = []
        
        if event.event_type == "org_chart_created":
            metrics.append(RealTimeMetric(
                name="org_charts_count",
                value=event.metric_value,
                trend="up",
                change_percent=5.0,
                updated_at=datetime.utcnow(),
                category="organizational"
            ))
        
        elif event.event_type == "scenario_calculated":
            metrics.append(RealTimeMetric(
                name="roi_calculations",
                value=event.metric_value,
                trend="up",
                change_percent=2.0,
                updated_at=datetime.utcnow(),
                category="financial"
            ))
        
        elif event.event_type == "compliance_check":
            metrics.append(RealTimeMetric(
                name="compliance_score",
                value=event.metric_value,
                trend="stable",
                change_percent=0.5,
                updated_at=datetime.utcnow(),
                category="compliance"
            ))
        
        return metrics
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for a specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def get_dashboard_template(self, template_id: str) -> Optional[DashboardTemplate]:
        """Get a dashboard template by ID"""
        return self.dashboard_templates.get(template_id)
    
    async def get_templates_for_user(self, user_role: str, institution_type: str) -> List[DashboardTemplate]:
        """Get dashboard templates suitable for a user"""
        suitable_templates = []
        
        for template in self.dashboard_templates.values():
            audience_ok = (
                (template.target_audience == user_role) or (template.target_audience == "all") or (user_role == "administrator")
            )
            type_ok = (
                (template.institution_type == institution_type) or (template.institution_type == "all")
            )
            if audience_ok and type_ok:
                suitable_templates.append(template)
        
        return suitable_templates
    
    async def create_custom_template(self, template: DashboardTemplate, user_id: str) -> str:
        """Create a custom dashboard template"""
        # In production, save to database
        template_id = f"custom_{user_id}_{datetime.utcnow().timestamp()}"
        template.id = template_id
        self.dashboard_templates[template_id] = template
        
        logger.info(f"Created custom template {template_id} for user {user_id}")
        return template_id
    
    # Analytics calculation methods
    async def get_compliance_score(self, user_id: str) -> float:
        """Calculate compliance score for a user.

        Placeholder: return 0.0 until sufficient data exists.
        """
        # TODO: compute from standards mappings + evidence coverage
        return 0.0
    
    async def get_active_standards_count(self, user_id: str) -> int:
        """Get count of active standards for a user.

        Placeholder: return 0 until documents are uploaded and processed.
        """
        return 0
    
    async def get_pending_actions_count(self, user_id: str) -> int:
        """Get count of pending actions for a user.

        Placeholder: return 0 until tasks are generated.
        """
        return 0
    
    async def get_recent_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent activity for a user.

        Placeholder: return empty list until events are tracked.
        """
        return []
    
    async def generate_advanced_analytics(self, user_id: str, time_range: str = "30d") -> Dict[str, Any]:
        """Generate advanced analytics insights.

        Placeholder skeleton until real analytics are computed.
        """
        return {
            "compliance_trends": {
                "current_score": 0.0,
                "trend": "stable",
                "change_over_period": 0.0,
                "projection": 0.0
            },
            "organizational_insights": {
                "structure_complexity": None,
                "compliance_distribution": {
                    "high_performers": 0,
                    "average_performers": 0,
                    "need_attention": 0
                },
                "recommendations": []
            },
            "predictive_analytics": {
                "risk_factors": [],
                "success_probability": None,
                "recommended_actions": []
            },
            "note": "Metrics will populate after you upload documents and begin activity."
        }


# Global analytics service instance
analytics_service = RealTimeAnalyticsService()


async def track_user_action(user_id: str, action_type: str, data: Dict[str, Any]):
    """Helper function to track user actions"""
    event = AnalyticsEvent(
        event_type=action_type,
        user_id=user_id,
        institution_id=data.get("institution_id"),
        timestamp=datetime.utcnow(),
        data=data,
        metric_name=data.get("metric_name", action_type),
        metric_value=data.get("metric_value", 1.0)
    )
    
    await analytics_service.track_event(event)
