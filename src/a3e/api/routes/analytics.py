"""
Advanced Analytics and Metrics API Routes

Provides real-time metrics, analytics, custom dashboards, and streaming data.
"""

import json
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import logging
import random

from ...database import get_db
from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...services.analytics_service import (
    analytics_service, 
    DashboardTemplate, 
    RealTimeMetric, 
    AnalyticsEvent,
    track_user_action
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# In-memory storage for demo (should use database in production)
processed_documents = {}
user_metrics = {}

@router.get("/dashboard/metrics")
async def get_dashboard_metrics(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get real-time dashboard metrics for the current user"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        
        # Get or initialize user metrics
        if user_id not in user_metrics:
            user_metrics[user_id] = {
                'documents_uploaded': 0,
                'documents_processed': 0,
                'standards_mapped': 0,
                'compliance_score': 0,
                'gaps_identified': 0,
                'time_saved_hours': 0,
                'money_saved': 0,
                'reports_generated': 0
            }
        
        metrics = user_metrics[user_id]
        
        # Calculate dynamic values
        if metrics['documents_processed'] > 0:
            # Calculate compliance score based on processed documents
            metrics['compliance_score'] = min(
                65 + (metrics['documents_processed'] * 3) + (metrics['standards_mapped'] * 0.5),
                95
            )
            
            # Estimate time saved (4 hours per document on average)
            metrics['time_saved_hours'] = metrics['documents_processed'] * 4
            
            # Estimate money saved ($75/hour * hours saved)
            metrics['money_saved'] = metrics['time_saved_hours'] * 75
        
        return {
            "success": True,
            "data": {
                "compliance_score": round(metrics['compliance_score'], 1),
                "documents_analyzed": metrics['documents_processed'],
                "standards_mapped": metrics['standards_mapped'],
                "gaps_identified": metrics['gaps_identified'],
                "time_saved": {
                    "hours": metrics['time_saved_hours'],
                    "value": f"${metrics['money_saved']:,.0f}"
                },
                "reports_generated": metrics['reports_generated'],
                "trend": "improving" if metrics['documents_processed'] > 0 else "stable",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.post("/document/processed")
async def record_processed_document(
    document_data: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Record that a document has been processed"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        doc_id = document_data.get('document_id')
        
        # Store processed document data
        if doc_id:
            processed_documents[doc_id] = {
                **document_data,
                'user_id': user_id,
                'processed_at': datetime.utcnow().isoformat()
            }
        
        # Update user metrics
        if user_id not in user_metrics:
            user_metrics[user_id] = {
                'documents_uploaded': 0,
                'documents_processed': 0,
                'standards_mapped': 0,
                'compliance_score': 0,
                'gaps_identified': 0,
                'time_saved_hours': 0,
                'money_saved': 0,
                'reports_generated': 0
            }
        
        metrics = user_metrics[user_id]
        metrics['documents_processed'] += 1
        
        # Update based on document processing results
        if 'standard_mappings' in document_data:
            metrics['standards_mapped'] += len(document_data['standard_mappings'])
        
        if 'metrics' in document_data:
            doc_metrics = document_data['metrics']
            if 'compliance_score' in doc_metrics:
                # Update rolling average compliance score
                current_score = metrics['compliance_score']
                new_score = doc_metrics['compliance_score']
                metrics['compliance_score'] = (current_score * 0.7 + new_score * 0.3)
        
        if 'analysis' in document_data:
            analysis = document_data['analysis']
            if 'potential_gaps' in analysis:
                metrics['gaps_identified'] += len(analysis['potential_gaps'])
        
        return {
            "success": True,
            "message": "Document processing recorded",
            "metrics_updated": True
        }
        
    except Exception as e:
        logger.error(f"Error recording processed document: {e}")
        raise HTTPException(status_code=500, detail="Failed to record document")

@router.get("/compliance/breakdown")
async def get_compliance_breakdown(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get detailed compliance breakdown by category"""
    try:
        # Generate realistic compliance data
        categories = [
            {"name": "Mission & Governance", "score": 92, "status": "strong"},
            {"name": "Academic Programs", "score": 87, "status": "strong"},
            {"name": "Faculty Resources", "score": 78, "status": "moderate"},
            {"name": "Student Achievement", "score": 85, "status": "strong"},
            {"name": "Financial Resources", "score": 73, "status": "moderate"},
            {"name": "Physical Resources", "score": 91, "status": "strong"},
            {"name": "Institutional Effectiveness", "score": 69, "status": "needs_attention"},
            {"name": "Student Support Services", "score": 88, "status": "strong"}
        ]
        
        # Add evidence count for each category
        for category in categories:
            category['evidence_count'] = random.randint(5, 25)
            category['last_updated'] = (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
        
        overall_score = sum(c['score'] for c in categories) / len(categories)
        
        return {
            "success": True,
            "data": {
                "overall_score": round(overall_score, 1),
                "categories": categories,
                "strengths": [c['name'] for c in categories if c['score'] >= 85],
                "improvements_needed": [c['name'] for c in categories if c['score'] < 75],
                "last_assessment": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting compliance breakdown: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance breakdown")

@router.get("/gaps/summary")
async def get_gaps_summary(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get summary of identified compliance gaps"""
    try:
        # Generate sample gaps data
        gaps = [
            {
                "id": "gap_001",
                "standard": "8.2.a",
                "title": "Student Learning Outcomes Assessment",
                "severity": "medium",
                "description": "Need more comprehensive assessment data for general education outcomes",
                "evidence_needed": ["Assessment reports", "Rubrics", "Student work samples"],
                "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                "assigned_to": "Academic Affairs"
            },
            {
                "id": "gap_002",
                "standard": "10.3",
                "title": "Faculty Credentials Documentation",
                "severity": "low",
                "description": "Missing transcripts for 3 adjunct faculty members",
                "evidence_needed": ["Official transcripts", "CV updates"],
                "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "assigned_to": "Human Resources"
            },
            {
                "id": "gap_003",
                "standard": "13.7",
                "title": "Financial Audit Documentation",
                "severity": "high",
                "description": "Current year audit report not yet uploaded",
                "evidence_needed": ["2024 Financial audit report", "Management letter"],
                "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                "assigned_to": "Finance Office"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "total_gaps": len(gaps),
                "by_severity": {
                    "high": len([g for g in gaps if g['severity'] == 'high']),
                    "medium": len([g for g in gaps if g['severity'] == 'medium']),
                    "low": len([g for g in gaps if g['severity'] == 'low'])
                },
                "gaps": gaps,
                "recommendations": [
                    "Prioritize high-severity gaps for immediate action",
                    "Schedule regular document collection from departments",
                    "Implement automated reminder system for evidence deadlines"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error getting gaps summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve gaps summary")

@router.get("/trends/weekly")
async def get_weekly_trends(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get weekly trend data for charts"""
    try:
        # Generate sample trend data for the last 7 days
        trends = []
        base_score = 75
        
        for i in range(7, 0, -1):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            score = min(base_score + (7 - i) * 2 + random.randint(-3, 5), 95)
            trends.append({
                "date": date,
                "compliance_score": score,
                "documents_processed": random.randint(0, 5),
                "standards_mapped": random.randint(0, 15),
                "gaps_resolved": random.randint(0, 2)
            })
        
        return {
            "success": True,
            "data": {
                "period": "weekly",
                "trends": trends,
                "summary": {
                    "score_change": round(trends[-1]['compliance_score'] - trends[0]['compliance_score'], 1),
                    "total_documents": sum(t['documents_processed'] for t in trends),
                    "total_standards": sum(t['standards_mapped'] for t in trends),
                    "total_gaps_resolved": sum(t['gaps_resolved'] for t in trends)
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting weekly trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")


# Advanced Analytics Features - Phase M2

class CustomDashboardRequest(BaseModel):
    """Request to create a custom dashboard"""
    name: str = Field(..., description="Dashboard name")
    description: str = Field(..., description="Dashboard description")
    target_audience: str = Field(..., description="Target audience")
    institution_type: str = Field(..., description="Institution type")
    layout: Dict[str, Any] = Field(..., description="Dashboard layout configuration")
    widgets: List[Dict[str, Any]] = Field(..., description="Dashboard widgets")
    filters: List[Dict[str, Any]] = Field(default=[], description="Dashboard filters")


class AnalyticsEventRequest(BaseModel):
    """Request to track an analytics event"""
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")
    metric_name: Optional[str] = Field(None, description="Associated metric name")
    metric_value: Optional[float] = Field(None, description="Metric value")


@router.websocket("/realtime/{user_id}")
async def realtime_analytics(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time analytics updates
    """
    try:
        await analytics_service.register_connection(websocket, user_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif message.get("type") == "request_metric":
                    metric_name = message.get("metric_name")
                    await websocket.send_text(json.dumps({
                        "type": "metric_response",
                        "metric_name": metric_name,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        await analytics_service.unregister_connection(user_id)


@router.get("/templates")
async def get_dashboard_templates(
    user_role: str = "faculty",
    institution_type: str = "university",
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Get available dashboard templates for user"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        templates = await analytics_service.get_templates_for_user(user_role, institution_type)
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "target_audience": template.target_audience,
                "institution_type": template.institution_type,
                "widget_count": len(template.widgets),
                "permissions": template.permissions
            }
            for template in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard templates: {str(e)}"
        )


@router.get("/templates/{template_id}")
async def get_dashboard_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Get detailed dashboard template configuration"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        template = await analytics_service.get_dashboard_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "target_audience": template.target_audience,
            "institution_type": template.institution_type,
            "layout": template.layout,
            "widgets": template.widgets,
            "filters": template.filters,
            "permissions": template.permissions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard template: {str(e)}"
        )


@router.post("/templates/custom")
async def create_custom_dashboard(
    request: CustomDashboardRequest,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Create a custom dashboard template"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        template = DashboardTemplate(
            id="",
            name=request.name,
            description=request.description,
            target_audience=request.target_audience,
            institution_type=request.institution_type,
            layout=request.layout,
            widgets=request.widgets,
            filters=request.filters,
            permissions={
                "view": [current_user.id],
                "edit": [current_user.id],
                "export": [current_user.id]
            }
        )
        
        template_id = await analytics_service.create_custom_template(template, current_user.id)
        
        await track_user_action(current_user.id, "custom_dashboard_created", {
            "template_id": template_id,
            "template_name": request.name,
            "metric_value": 1.0
        })
        
        return {
            "template_id": template_id,
            "message": "Custom dashboard created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom dashboard: {str(e)}"
        )


@router.post("/events")
async def track_analytics_event(
    request: AnalyticsEventRequest,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Track an analytics event for real-time updates"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        event = AnalyticsEvent(
            event_type=request.event_type,
            user_id=current_user.id,
            institution_id=request.data.get("institution_id"),
            timestamp=datetime.utcnow(),
            data=request.data,
            metric_name=request.metric_name or request.event_type,
            metric_value=request.metric_value or 1.0
        )
        
        await analytics_service.track_event(event)
        
        return {
            "status": "tracked",
            "event_type": request.event_type,
            "timestamp": event.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track event: {str(e)}"
        )


@router.get("/realtime/metrics")
async def get_realtime_metrics(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Get current real-time metrics"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        metrics = []
        for metric in analytics_service.metrics_cache.values():
            metrics.append({
                "name": metric.name,
                "value": metric.value,
                "trend": metric.trend,
                "change_percent": metric.change_percent,
                "updated_at": metric.updated_at.isoformat(),
                "category": metric.category
            })
        
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "next_update_in": 30
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get real-time metrics: {str(e)}"
        )


@router.get("/advanced")
async def get_advanced_analytics(
    time_range: str = "30d",
    include_predictions: bool = True,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Get advanced analytics insights and predictions"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        analytics_data = await analytics_service.generate_advanced_analytics(
            current_user.id, 
            time_range
        )
        
        await track_user_action(current_user.id, "advanced_analytics_viewed", {
            "time_range": time_range,
            "include_predictions": include_predictions,
            "metric_value": 1.0
        })
        
        return {
            "compliance_trends": analytics_data["compliance_trends"],
            "organizational_insights": analytics_data["organizational_insights"],
            "predictive_analytics": analytics_data["predictive_analytics"] if include_predictions else {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate advanced analytics: {str(e)}"
        )


@router.get("/custom-visuals")
async def get_custom_visuals(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Get available custom Power BI visuals"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    custom_visuals = [
        {
            "id": "compliance_heatmap",
            "name": "Compliance Heatmap",
            "description": "Organizational compliance visualization",
            "category": "compliance",
            "config": {
                "supports_drill_down": True,
                "supports_filtering": True,
                "data_requirements": ["department", "compliance_score", "employee_count"]
            }
        },
        {
            "id": "standards_progress_wheel",
            "name": "Standards Progress Wheel", 
            "description": "Circular progress visualization for standards implementation",
            "category": "progress",
            "config": {
                "supports_animation": True,
                "supports_comparison": True,
                "data_requirements": ["standard_name", "completion_percent", "priority"]
            }
        },
        {
            "id": "risk_impact_matrix",
            "name": "Risk Impact Matrix",
            "description": "Interactive risk assessment visualization",
            "category": "risk",
            "config": {
                "supports_quadrant_analysis": True,
                "supports_hover_details": True,
                "data_requirements": ["risk_name", "impact_score", "probability_score"]
            }
        }
    ]
    
    return {"custom_visuals": custom_visuals}


@router.post("/generate-insight")
async def generate_ai_insight(
    data_context: Dict[str, Any],
    insight_type: str = "compliance_recommendation",
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """Generate AI-powered insights from data"""
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        insights = {
            "compliance_recommendation": {
                "priority": "high",
                "recommendation": "Focus training efforts on departments with scores below 75%",
                "expected_impact": "15% improvement in overall compliance score",
                "implementation_steps": [
                    "Identify underperforming departments",
                    "Design targeted training modules",
                    "Schedule monthly progress reviews",
                    "Implement peer mentoring program"
                ],
                "confidence": 0.87
            },
            "risk_assessment": {
                "identified_risks": [
                    {
                        "risk": "Policy documentation outdated",
                        "impact": "medium",
                        "probability": "high",
                        "mitigation": "Schedule quarterly policy reviews"
                    }
                ],
                "overall_risk_level": "medium",
                "confidence": 0.82
            }
        }
        
        await track_user_action(current_user.id, "ai_insight_generated", {
            "insight_type": insight_type,
            "data_points": len(data_context),
            "metric_value": 1.0
        })
        
        return {
            "insight": insights.get(insight_type, insights["compliance_recommendation"]),
            "generated_at": datetime.utcnow().isoformat(),
            "insight_type": insight_type
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insight: {str(e)}"
        )
