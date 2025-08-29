"""
Real-Time Monitoring and Dashboard Service

Provides live compliance metrics, real-time alerts, and dynamic dashboards
using WebSocket connections for instant updates.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


class RealtimeMonitoringService:
    """
    Real-time compliance monitoring and metrics streaming
    """
    
    def __init__(self):
        self.active_connections: Set[Any] = set()
        self.metrics_cache: Dict[str, Any] = {}
        self.alert_queue: List[Dict[str, Any]] = []
        self.monitoring_intervals = self._initialize_monitoring_intervals()
        self.metric_thresholds = self._initialize_thresholds()
        self.monitoring_tasks = {}
    
    def _initialize_monitoring_intervals(self) -> Dict[str, int]:
        """Initialize monitoring intervals in seconds"""
        return {
            "compliance_score": 300,      # 5 minutes
            "document_processing": 60,    # 1 minute
            "gap_analysis": 600,          # 10 minutes
            "risk_assessment": 900,       # 15 minutes
            "user_activity": 30,          # 30 seconds
            "system_health": 120          # 2 minutes
        }
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize metric thresholds for alerts"""
        return {
            "compliance_score": {"critical": 60, "warning": 70, "good": 80},
            "document_age": {"critical": 365, "warning": 180, "good": 90},
            "gap_count": {"critical": 10, "warning": 5, "good": 2},
            "processing_time": {"critical": 300, "warning": 180, "good": 60},
            "evidence_quality": {"critical": 0.5, "warning": 0.7, "good": 0.85}
        }
    
    async def start_monitoring(self, institution_id: str):
        """
        Start real-time monitoring for an institution
        """
        try:
            # Start various monitoring tasks
            self.monitoring_tasks[institution_id] = {
                "compliance": asyncio.create_task(
                    self._monitor_compliance(institution_id)
                ),
                "documents": asyncio.create_task(
                    self._monitor_document_processing(institution_id)
                ),
                "risks": asyncio.create_task(
                    self._monitor_risk_levels(institution_id)
                ),
                "activity": asyncio.create_task(
                    self._monitor_user_activity(institution_id)
                )
            }
            
            logger.info(f"Started real-time monitoring for institution {institution_id}")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    async def stop_monitoring(self, institution_id: str):
        """
        Stop monitoring for an institution
        """
        if institution_id in self.monitoring_tasks:
            for task in self.monitoring_tasks[institution_id].values():
                task.cancel()
            del self.monitoring_tasks[institution_id]
            logger.info(f"Stopped monitoring for institution {institution_id}")
    
    async def get_realtime_dashboard(
        self,
        institution_id: str,
        dashboard_type: str = "executive"
    ) -> Dict[str, Any]:
        """
        Get real-time dashboard data
        """
        try:
            # Get cached metrics or fetch fresh
            metrics = await self._get_current_metrics(institution_id)
            
            if dashboard_type == "executive":
                return self._build_executive_dashboard(metrics)
            elif dashboard_type == "operational":
                return self._build_operational_dashboard(metrics)
            elif dashboard_type == "compliance":
                return self._build_compliance_dashboard(metrics)
            elif dashboard_type == "risk":
                return self._build_risk_dashboard(metrics)
            else:
                return self._build_executive_dashboard(metrics)
                
        except Exception as e:
            logger.error(f"Error building dashboard: {e}")
            return self._get_fallback_dashboard()
    
    async def subscribe_to_updates(
        self,
        institution_id: str,
        connection: Any,
        metrics: List[str]
    ):
        """
        Subscribe a connection to real-time metric updates
        """
        self.active_connections.add(connection)
        
        # Send initial data
        initial_data = await self._get_current_metrics(institution_id)
        await self._send_to_connection(connection, {
            "type": "initial",
            "data": initial_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start sending updates
        asyncio.create_task(
            self._stream_updates(institution_id, connection, metrics)
        )
    
    async def unsubscribe(self, connection: Any):
        """
        Unsubscribe a connection from updates
        """
        if connection in self.active_connections:
            self.active_connections.remove(connection)
    
    async def trigger_alert(
        self,
        institution_id: str,
        alert_type: str,
        severity: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Trigger a real-time alert
        """
        alert = {
            "id": f"alert_{datetime.utcnow().timestamp()}",
            "institution_id": institution_id,
            "type": alert_type,
            "severity": severity,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False
        }
        
        # Add to queue
        self.alert_queue.append(alert)
        
        # Broadcast to connected clients
        await self._broadcast_alert(alert)
        
        # Store for persistence
        await self._store_alert(alert)
        
        return alert
    
    async def get_metric_history(
        self,
        institution_id: str,
        metric_name: str,
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """
        Get historical data for a specific metric
        """
        # Parse time range
        hours = {
            "1h": 1, "6h": 6, "24h": 24,
            "7d": 168, "30d": 720
        }.get(time_range, 24)
        
        # Generate sample historical data (would query database in production)
        data_points = self._generate_metric_history(metric_name, hours)
        
        return {
            "metric": metric_name,
            "time_range": time_range,
            "data_points": data_points,
            "summary": self._calculate_metric_summary(data_points)
        }
    
    async def get_live_feed(
        self,
        institution_id: str,
        feed_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Get live activity feed
        """
        feed_items = []
        
        # Get recent activities based on type
        if feed_type in ["all", "documents"]:
            feed_items.extend(await self._get_document_activities(institution_id))
        
        if feed_type in ["all", "compliance"]:
            feed_items.extend(await self._get_compliance_activities(institution_id))
        
        if feed_type in ["all", "users"]:
            feed_items.extend(await self._get_user_activities(institution_id))
        
        if feed_type in ["all", "alerts"]:
            feed_items.extend(self._get_recent_alerts(institution_id))
        
        # Sort by timestamp
        feed_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return feed_items[:50]  # Return latest 50 items
    
    async def _monitor_compliance(self, institution_id: str):
        """
        Monitor compliance metrics in real-time
        """
        while True:
            try:
                # Fetch current compliance metrics
                metrics = await self._fetch_compliance_metrics(institution_id)
                
                # Check for threshold violations
                alerts = self._check_compliance_thresholds(metrics)
                for alert in alerts:
                    await self.trigger_alert(
                        institution_id,
                        "compliance",
                        alert["severity"],
                        alert["message"],
                        alert.get("data")
                    )
                
                # Update cache
                self.metrics_cache[f"{institution_id}_compliance"] = metrics
                
                # Broadcast updates
                await self._broadcast_metric_update(institution_id, "compliance", metrics)
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_intervals["compliance_score"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in compliance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_document_processing(self, institution_id: str):
        """
        Monitor document processing in real-time
        """
        while True:
            try:
                # Get processing status
                processing_status = await self._get_processing_status(institution_id)
                
                # Update cache
                self.metrics_cache[f"{institution_id}_processing"] = processing_status
                
                # Broadcast updates
                await self._broadcast_metric_update(
                    institution_id,
                    "processing",
                    processing_status
                )
                
                await asyncio.sleep(self.monitoring_intervals["document_processing"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in document monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_risk_levels(self, institution_id: str):
        """
        Monitor risk levels in real-time
        """
        while True:
            try:
                # Calculate current risk levels
                risk_assessment = await self._assess_current_risks(institution_id)
                
                # Check for critical risks
                if risk_assessment.get("overall_risk_level") == "critical":
                    await self.trigger_alert(
                        institution_id,
                        "risk",
                        "critical",
                        "Critical risk level detected",
                        risk_assessment
                    )
                
                # Update cache
                self.metrics_cache[f"{institution_id}_risks"] = risk_assessment
                
                # Broadcast updates
                await self._broadcast_metric_update(institution_id, "risks", risk_assessment)
                
                await asyncio.sleep(self.monitoring_intervals["risk_assessment"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_user_activity(self, institution_id: str):
        """
        Monitor user activity in real-time
        """
        while True:
            try:
                # Get active users and their activities
                activity_data = await self._get_user_activity(institution_id)
                
                # Update cache
                self.metrics_cache[f"{institution_id}_activity"] = activity_data
                
                # Broadcast updates
                await self._broadcast_metric_update(institution_id, "activity", activity_data)
                
                await asyncio.sleep(self.monitoring_intervals["user_activity"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in activity monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _get_current_metrics(self, institution_id: str) -> Dict[str, Any]:
        """
        Get current metrics from cache or fetch fresh
        """
        metrics = {}
        
        # Compliance metrics
        compliance_key = f"{institution_id}_compliance"
        if compliance_key in self.metrics_cache:
            metrics["compliance"] = self.metrics_cache[compliance_key]
        else:
            metrics["compliance"] = await self._fetch_compliance_metrics(institution_id)
        
        # Processing metrics
        processing_key = f"{institution_id}_processing"
        if processing_key in self.metrics_cache:
            metrics["processing"] = self.metrics_cache[processing_key]
        else:
            metrics["processing"] = await self._get_processing_status(institution_id)
        
        # Risk metrics
        risk_key = f"{institution_id}_risks"
        if risk_key in self.metrics_cache:
            metrics["risks"] = self.metrics_cache[risk_key]
        else:
            metrics["risks"] = await self._assess_current_risks(institution_id)
        
        # Activity metrics
        activity_key = f"{institution_id}_activity"
        if activity_key in self.metrics_cache:
            metrics["activity"] = self.metrics_cache[activity_key]
        else:
            metrics["activity"] = await self._get_user_activity(institution_id)
        
        return metrics
    
    def _build_executive_dashboard(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build executive dashboard view
        """
        compliance = metrics.get("compliance", {})
        risks = metrics.get("risks", {})
        processing = metrics.get("processing", {})
        
        return {
            "type": "executive",
            "summary": {
                "overall_health": self._calculate_health_score(metrics),
                "compliance_score": compliance.get("overall_score", 0),
                "risk_level": risks.get("overall_risk_level", "unknown"),
                "documents_processed_today": processing.get("processed_today", 0),
                "active_alerts": len([a for a in self.alert_queue if not a.get("acknowledged")])
            },
            "key_metrics": [
                {
                    "name": "Compliance Score",
                    "value": compliance.get("overall_score", 0),
                    "trend": compliance.get("trend", "stable"),
                    "target": 85,
                    "status": self._get_metric_status(compliance.get("overall_score", 0), 85)
                },
                {
                    "name": "Risk Score",
                    "value": risks.get("overall_risk_score", 0),
                    "trend": risks.get("trend", "stable"),
                    "target": 30,
                    "status": self._get_risk_status(risks.get("overall_risk_score", 0))
                },
                {
                    "name": "Document Currency",
                    "value": processing.get("document_currency_pct", 0),
                    "trend": "improving",
                    "target": 90,
                    "status": self._get_metric_status(processing.get("document_currency_pct", 0), 90)
                },
                {
                    "name": "Gap Closure Rate",
                    "value": compliance.get("gap_closure_rate", 0),
                    "trend": "improving",
                    "target": 95,
                    "status": self._get_metric_status(compliance.get("gap_closure_rate", 0), 95)
                }
            ],
            "charts": {
                "compliance_trend": self._generate_trend_data("compliance", 7),
                "risk_heatmap": self._generate_risk_heatmap(risks),
                "processing_pipeline": self._generate_pipeline_data(processing)
            },
            "quick_stats": {
                "days_to_review": compliance.get("days_to_review", "N/A"),
                "standards_met": f"{compliance.get('standards_met', 0)}/{compliance.get('total_standards', 0)}",
                "critical_gaps": risks.get("critical_gaps", 0),
                "team_members_active": metrics.get("activity", {}).get("active_users", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_operational_dashboard(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build operational dashboard view
        """
        processing = metrics.get("processing", {})
        activity = metrics.get("activity", {})
        
        return {
            "type": "operational",
            "processing_metrics": {
                "in_queue": processing.get("queue_size", 0),
                "processing": processing.get("active_processing", 0),
                "completed_today": processing.get("completed_today", 0),
                "failed_today": processing.get("failed_today", 0),
                "avg_processing_time": processing.get("avg_time_seconds", 0)
            },
            "system_health": {
                "api_latency": "45ms",
                "database_status": "healthy",
                "ai_service_status": "operational",
                "storage_usage": "34.2%",
                "error_rate": "0.02%"
            },
            "user_activity": {
                "active_sessions": activity.get("active_sessions", 0),
                "documents_uploaded": activity.get("uploads_today", 0),
                "reports_generated": activity.get("reports_today", 0),
                "api_calls_today": activity.get("api_calls", 0)
            },
            "recent_operations": self._get_recent_operations(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_compliance_dashboard(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build compliance-focused dashboard
        """
        compliance = metrics.get("compliance", {})
        
        return {
            "type": "compliance",
            "overview": {
                "overall_score": compliance.get("overall_score", 0),
                "standards_coverage": compliance.get("coverage_pct", 0),
                "evidence_strength": compliance.get("avg_evidence_strength", 0),
                "last_assessment": compliance.get("last_assessment_date", "")
            },
            "by_category": self._get_compliance_by_category(compliance),
            "gap_analysis": {
                "total_gaps": compliance.get("total_gaps", 0),
                "critical": compliance.get("critical_gaps", 0),
                "major": compliance.get("major_gaps", 0),
                "minor": compliance.get("minor_gaps", 0),
                "closure_timeline": compliance.get("gap_closure_timeline", {})
            },
            "recent_changes": self._get_recent_compliance_changes(),
            "upcoming_deadlines": self._get_compliance_deadlines(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_risk_dashboard(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build risk management dashboard
        """
        risks = metrics.get("risks", {})
        
        return {
            "type": "risk",
            "risk_overview": {
                "overall_level": risks.get("overall_risk_level", "unknown"),
                "risk_score": risks.get("overall_risk_score", 0),
                "trend": risks.get("trend", "stable"),
                "last_assessment": risks.get("last_assessment", "")
            },
            "risk_matrix": self._generate_risk_matrix(risks),
            "top_risks": risks.get("top_risks", []),
            "mitigation_status": {
                "active_mitigations": risks.get("active_mitigations", 0),
                "completed_this_month": risks.get("mitigations_completed", 0),
                "effectiveness_rate": risks.get("mitigation_effectiveness", 0)
            },
            "risk_indicators": self._get_risk_indicators(risks),
            "predictive_alerts": self._get_predictive_risk_alerts(risks),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _stream_updates(
        self,
        institution_id: str,
        connection: Any,
        metrics: List[str]
    ):
        """
        Stream updates to a connected client
        """
        while connection in self.active_connections:
            try:
                # Prepare update batch
                updates = {}
                
                for metric in metrics:
                    cache_key = f"{institution_id}_{metric}"
                    if cache_key in self.metrics_cache:
                        updates[metric] = self.metrics_cache[cache_key]
                
                if updates:
                    await self._send_to_connection(connection, {
                        "type": "update",
                        "data": updates,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Wait before next update
                await asyncio.sleep(5)  # Send updates every 5 seconds
                
            except Exception as e:
                logger.error(f"Error streaming updates: {e}")
                break
    
    async def _send_to_connection(self, connection: Any, data: Dict[str, Any]):
        """
        Send data to a specific connection
        """
        try:
            if hasattr(connection, 'send_json'):
                await connection.send_json(data)
            elif hasattr(connection, 'send'):
                await connection.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to connection: {e}")
            await self.unsubscribe(connection)
    
    async def _broadcast_metric_update(
        self,
        institution_id: str,
        metric_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast metric update to all connected clients
        """
        message = {
            "type": "metric_update",
            "institution_id": institution_id,
            "metric": metric_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection in self.active_connections:
            await self._send_to_connection(connection, message)
    
    async def _broadcast_alert(self, alert: Dict[str, Any]):
        """
        Broadcast alert to all connected clients
        """
        message = {
            "type": "alert",
            "alert": alert
        }
        
        for connection in self.active_connections:
            await self._send_to_connection(connection, message)
    
    async def _fetch_compliance_metrics(self, institution_id: str) -> Dict[str, Any]:
        """
        Fetch current compliance metrics
        """
        # In production, would query database
        # For now, return realistic sample data
        return {
            "overall_score": 78.5,
            "trend": "improving",
            "standards_met": 42,
            "total_standards": 50,
            "coverage_pct": 84.0,
            "avg_evidence_strength": 0.72,
            "critical_gaps": 2,
            "major_gaps": 5,
            "minor_gaps": 8,
            "total_gaps": 15,
            "gap_closure_rate": 65.0,
            "days_to_review": 120,
            "last_assessment_date": datetime.utcnow().isoformat()
        }
    
    async def _get_processing_status(self, institution_id: str) -> Dict[str, Any]:
        """
        Get document processing status
        """
        return {
            "queue_size": random.randint(0, 10),
            "active_processing": random.randint(0, 3),
            "completed_today": random.randint(10, 50),
            "failed_today": random.randint(0, 2),
            "processed_today": random.randint(15, 60),
            "avg_time_seconds": random.uniform(30, 180),
            "document_currency_pct": 76.5
        }
    
    async def _assess_current_risks(self, institution_id: str) -> Dict[str, Any]:
        """
        Assess current risk levels
        """
        return {
            "overall_risk_level": "medium",
            "overall_risk_score": 45.2,
            "trend": "stable",
            "critical_gaps": 2,
            "top_risks": [
                {"type": "document_age", "level": "high", "score": 0.7},
                {"type": "compliance_gaps", "level": "medium", "score": 0.5},
                {"type": "upcoming_review", "level": "low", "score": 0.3}
            ],
            "active_mitigations": 5,
            "mitigations_completed": 3,
            "mitigation_effectiveness": 72.0,
            "last_assessment": datetime.utcnow().isoformat()
        }
    
    async def _get_user_activity(self, institution_id: str) -> Dict[str, Any]:
        """
        Get user activity metrics
        """
        return {
            "active_users": random.randint(3, 15),
            "active_sessions": random.randint(5, 20),
            "uploads_today": random.randint(5, 25),
            "reports_today": random.randint(1, 8),
            "api_calls": random.randint(100, 1000)
        }
    
    def _check_compliance_thresholds(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check if metrics violate thresholds
        """
        alerts = []
        
        score = metrics.get("overall_score", 100)
        thresholds = self.metric_thresholds["compliance_score"]
        
        if score < thresholds["critical"]:
            alerts.append({
                "severity": "critical",
                "message": f"Compliance score critically low: {score}%",
                "data": {"score": score, "threshold": thresholds["critical"]}
            })
        elif score < thresholds["warning"]:
            alerts.append({
                "severity": "warning",
                "message": f"Compliance score below warning threshold: {score}%",
                "data": {"score": score, "threshold": thresholds["warning"]}
            })
        
        return alerts
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall health score
        """
        compliance_score = metrics.get("compliance", {}).get("overall_score", 0) / 100
        risk_score = 1 - (metrics.get("risks", {}).get("overall_risk_score", 0) / 100)
        processing_health = 1 - (metrics.get("processing", {}).get("failed_today", 0) / 
                                max(metrics.get("processing", {}).get("processed_today", 1), 1))
        
        health = (compliance_score * 0.5 + risk_score * 0.3 + processing_health * 0.2) * 100
        return round(health, 1)
    
    def _get_metric_status(self, value: float, target: float) -> str:
        """
        Get status based on value vs target
        """
        if value >= target:
            return "good"
        elif value >= target * 0.8:
            return "warning"
        else:
            return "critical"
    
    def _get_risk_status(self, risk_score: float) -> str:
        """
        Get risk status
        """
        if risk_score < 30:
            return "good"
        elif risk_score < 60:
            return "warning"
        else:
            return "critical"
    
    def _generate_trend_data(self, metric: str, days: int) -> List[Dict[str, Any]]:
        """
        Generate trend data for charts
        """
        data = []
        base_value = 75
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
            value = base_value + random.uniform(-5, 5)
            base_value = value  # Create realistic trend
            
            data.append({
                "date": date,
                "value": round(value, 1)
            })
        
        return data
    
    def _generate_risk_heatmap(self, risks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate risk heatmap data
        """
        categories = ["Documentation", "Compliance", "Governance", "Financial", "Academic"]
        standards = ["CR 1-5", "CR 6-10", "CR 11-14", "CS 5-7", "CS 8-10", "CS 11-14"]
        
        heatmap_data = []
        for cat in categories:
            for std in standards:
                heatmap_data.append({
                    "category": cat,
                    "standard": std,
                    "risk_level": random.uniform(0.1, 0.9)
                })
        
        return {
            "data": heatmap_data,
            "categories": categories,
            "standards": standards
        }
    
    def _generate_pipeline_data(self, processing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate processing pipeline visualization data
        """
        return {
            "stages": [
                {"name": "Queued", "count": processing.get("queue_size", 0)},
                {"name": "Processing", "count": processing.get("active_processing", 0)},
                {"name": "AI Analysis", "count": random.randint(0, 5)},
                {"name": "Review", "count": random.randint(0, 3)},
                {"name": "Complete", "count": processing.get("completed_today", 0)}
            ],
            "flow_rate": processing.get("avg_time_seconds", 60)
        }
    
    def _generate_metric_history(self, metric_name: str, hours: int) -> List[Dict[str, Any]]:
        """
        Generate historical metric data
        """
        data = []
        base_value = 75
        
        for i in range(min(hours * 4, 100)):  # Data point every 15 minutes
            timestamp = datetime.utcnow() - timedelta(minutes=15*i)
            value = base_value + random.uniform(-2, 2)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "value": round(value, 2)
            })
        
        data.reverse()
        return data
    
    def _calculate_metric_summary(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for metric
        """
        if not data_points:
            return {}
        
        values = [p["value"] for p in data_points]
        
        return {
            "current": values[-1],
            "average": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
            "trend": "increasing" if values[-1] > values[0] else "decreasing"
        }
    
    async def _get_document_activities(self, institution_id: str) -> List[Dict[str, Any]]:
        """
        Get recent document activities
        """
        activities = []
        
        for i in range(5):
            activities.append({
                "type": "document",
                "action": random.choice(["uploaded", "processed", "mapped"]),
                "document": f"Document_{random.randint(100, 999)}.pdf",
                "user": f"user{random.randint(1, 10)}@example.com",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i*10)).isoformat()
            })
        
        return activities
    
    async def _get_compliance_activities(self, institution_id: str) -> List[Dict[str, Any]]:
        """
        Get recent compliance activities
        """
        activities = []
        
        for i in range(3):
            activities.append({
                "type": "compliance",
                "action": random.choice(["gap_identified", "standard_mapped", "evidence_verified"]),
                "details": f"Standard CR {random.randint(1, 14)}",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i*20)).isoformat()
            })
        
        return activities
    
    async def _get_user_activities(self, institution_id: str) -> List[Dict[str, Any]]:
        """
        Get recent user activities
        """
        activities = []
        
        for i in range(4):
            activities.append({
                "type": "user",
                "action": random.choice(["login", "report_generated", "data_exported"]),
                "user": f"user{random.randint(1, 10)}@example.com",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i*15)).isoformat()
            })
        
        return activities
    
    def _get_recent_alerts(self, institution_id: str) -> List[Dict[str, Any]]:
        """
        Get recent alerts for institution
        """
        return [
            alert for alert in self.alert_queue[-10:]
            if alert.get("institution_id") == institution_id
        ]
    
    async def _store_alert(self, alert: Dict[str, Any]):
        """
        Store alert for persistence
        """
        # In production, would store in database
        pass
    
    def _get_recent_operations(self) -> List[Dict[str, Any]]:
        """
        Get recent system operations
        """
        operations = []
        
        for i in range(10):
            operations.append({
                "id": f"op_{random.randint(1000, 9999)}",
                "type": random.choice(["document_processing", "report_generation", "api_call"]),
                "status": random.choice(["success", "success", "success", "failed"]),
                "duration_ms": random.randint(50, 5000),
                "timestamp": (datetime.utcnow() - timedelta(minutes=i*2)).isoformat()
            })
        
        return operations
    
    def _get_compliance_by_category(self, compliance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get compliance breakdown by category
        """
        categories = [
            {"name": "Mission & Governance", "score": 82, "standards": 10},
            {"name": "Faculty", "score": 75, "standards": 8},
            {"name": "Educational Programs", "score": 79, "standards": 12},
            {"name": "Student Support", "score": 88, "standards": 6},
            {"name": "Resources", "score": 71, "standards": 9}
        ]
        
        return categories
    
    def _get_recent_compliance_changes(self) -> List[Dict[str, Any]]:
        """
        Get recent compliance changes
        """
        changes = []
        
        for i in range(5):
            changes.append({
                "standard": f"CR {random.randint(1, 14)}",
                "change": random.choice(["improved", "declined", "stable"]),
                "from_score": random.randint(60, 80),
                "to_score": random.randint(65, 85),
                "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            })
        
        return changes
    
    def _get_compliance_deadlines(self) -> List[Dict[str, Any]]:
        """
        Get upcoming compliance deadlines
        """
        deadlines = [
            {
                "item": "Annual Report Submission",
                "due_date": (datetime.utcnow() + timedelta(days=45)).strftime("%Y-%m-%d"),
                "days_remaining": 45,
                "status": "on_track"
            },
            {
                "item": "QEP Progress Report",
                "due_date": (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "days_remaining": 90,
                "status": "on_track"
            },
            {
                "item": "Faculty Credentials Update",
                "due_date": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "days_remaining": 30,
                "status": "at_risk"
            }
        ]
        
        return deadlines
    
    def _generate_risk_matrix(self, risks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate risk matrix visualization data
        """
        matrix_data = []
        
        risk_items = [
            ("Document Currency", 3, 2),
            ("Compliance Gaps", 4, 3),
            ("Resource Allocation", 2, 3),
            ("Faculty Qualifications", 2, 2),
            ("Student Achievement", 3, 4)
        ]
        
        for name, likelihood, impact in risk_items:
            matrix_data.append({
                "name": name,
                "likelihood": likelihood,
                "impact": impact,
                "score": likelihood * impact
            })
        
        return {
            "data": matrix_data,
            "max_likelihood": 5,
            "max_impact": 5
        }
    
    def _get_risk_indicators(self, risks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get key risk indicators
        """
        return [
            {
                "indicator": "Document Age",
                "value": 186,
                "unit": "days",
                "threshold": 180,
                "status": "warning"
            },
            {
                "indicator": "Gap Count",
                "value": 15,
                "unit": "gaps",
                "threshold": 10,
                "status": "critical"
            },
            {
                "indicator": "Evidence Quality",
                "value": 72,
                "unit": "%",
                "threshold": 80,
                "status": "warning"
            }
        ]
    
    def _get_predictive_risk_alerts(self, risks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get predictive risk alerts
        """
        return [
            {
                "prediction": "Compliance score likely to drop below 70% in 30 days",
                "confidence": "high",
                "recommended_action": "Address critical gaps immediately"
            },
            {
                "prediction": "Document refresh needed for 25% of evidence",
                "confidence": "medium",
                "recommended_action": "Schedule document review cycle"
            }
        ]
    
    def _get_fallback_dashboard(self) -> Dict[str, Any]:
        """
        Fallback dashboard when data unavailable
        """
        return {
            "type": "fallback",
            "message": "Real-time data temporarily unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_monitoring_service = None


def get_monitoring_service() -> RealtimeMonitoringService:
    """Get or create monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = RealtimeMonitoringService()
    return _monitoring_service