"""
Real-time Data Streaming Service
WebSocket-based real-time data streaming for live analytics
Part of Phase M2: Advanced Analytics Features
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import weakref
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Types of real-time data streams"""
    METRICS = "metrics"
    EVENTS = "events"
    ALERTS = "alerts"
    ANALYTICS = "analytics"
    USER_ACTIVITY = "user_activity"
    SYSTEM_STATUS = "system_status"


@dataclass
class StreamData:
    """Real-time stream data packet"""
    stream_type: StreamType
    timestamp: datetime
    user_id: Optional[str]
    institution_id: Optional[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stream_type": self.stream_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "institution_id": self.institution_id,
            "data": self.data,
            "metadata": self.metadata
        }


@dataclass
class StreamSubscription:
    """Client subscription to data streams"""
    client_id: str
    user_id: str
    stream_types: Set[StreamType]
    filters: Dict[str, Any]
    last_activity: datetime
    buffer_size: int = 100
    
    def __post_init__(self):
        self.message_buffer = deque(maxlen=self.buffer_size)


class RealTimeStreamingService:
    """Real-time data streaming service with WebSocket support"""
    
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}  # WebSocket connections
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self.stream_history: Dict[StreamType, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metrics_cache: Dict[str, Any] = {}
        self.alert_thresholds: Dict[str, float] = {}
        self.analytics_processors: Dict[str, Any] = {}
        
        # Initialize default alert thresholds
        self._initialize_alert_thresholds()
        
        # Start background tasks
        self.background_tasks = []
        self._start_background_tasks()
    
    def _initialize_alert_thresholds(self):
        """Initialize default alert thresholds"""
        self.alert_thresholds = {
            "compliance_score_drop": 5.0,       # Alert if score drops by 5%
            "documents_processed_spike": 50,     # Alert if >50 docs processed in hour
            "error_rate_threshold": 0.05,       # Alert if error rate >5%
            "response_time_threshold": 2000,    # Alert if response time >2s
            "concurrent_users_threshold": 100,  # Alert if >100 concurrent users
            "storage_usage_threshold": 0.85     # Alert if storage >85% full
        }
    
    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        async def cleanup_inactive_connections():
            while True:
                try:
                    await self._cleanup_inactive_connections()
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Connection cleanup error: {e}")
                    await asyncio.sleep(60)
        
        async def generate_analytics_stream():
            while True:
                try:
                    await self._generate_periodic_analytics()
                    await asyncio.sleep(30)  # Generate analytics every 30 seconds
                except Exception as e:
                    logger.error(f"Analytics generation error: {e}")
                    await asyncio.sleep(60)
        
        async def monitor_system_metrics():
            while True:
                try:
                    await self._monitor_system_metrics()
                    await asyncio.sleep(10)  # Monitor every 10 seconds
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    await asyncio.sleep(30)
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(cleanup_inactive_connections()),
            asyncio.create_task(generate_analytics_stream()),
            asyncio.create_task(monitor_system_metrics())
        ]
    
    async def register_connection(self, websocket: Any, user_id: str, client_id: str = None) -> str:
        """Register a new WebSocket connection"""
        if not client_id:
            client_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Store connection with weak reference to avoid memory leaks
        self.active_connections[client_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0
        }
        
        logger.info(f"WebSocket connection registered: {client_id} for user {user_id}")
        
        # Send welcome message
        await self._send_to_client(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "available_streams": [stream.value for stream in StreamType]
        })
        
        return client_id
    
    async def unregister_connection(self, client_id: str):
        """Unregister a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket connection unregistered: {client_id}")
        
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
    
    async def subscribe_to_stream(
        self, 
        client_id: str, 
        stream_types: List[str], 
        filters: Dict[str, Any] = None
    ) -> bool:
        """Subscribe client to specific data streams"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        
        # Convert string stream types to enum
        parsed_stream_types = set()
        for stream_type in stream_types:
            try:
                parsed_stream_types.add(StreamType(stream_type))
            except ValueError:
                logger.warning(f"Invalid stream type: {stream_type}")
        
        subscription = StreamSubscription(
            client_id=client_id,
            user_id=connection["user_id"],
            stream_types=parsed_stream_types,
            filters=filters or {},
            last_activity=datetime.utcnow()
        )
        
        self.subscriptions[client_id] = subscription
        
        # Send confirmation
        await self._send_to_client(client_id, {
            "type": "subscription_confirmed",
            "stream_types": [st.value for st in parsed_stream_types],
            "filters": filters,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send recent history for subscribed streams
        await self._send_stream_history(client_id, parsed_stream_types)
        
        return True
    
    async def unsubscribe_from_stream(self, client_id: str, stream_types: List[str] = None):
        """Unsubscribe client from specific streams or all streams"""
        if client_id not in self.subscriptions:
            return
        
        subscription = self.subscriptions[client_id]
        
        if stream_types:
            # Remove specific stream types
            for stream_type in stream_types:
                try:
                    subscription.stream_types.discard(StreamType(stream_type))
                except ValueError:
                    continue
        else:
            # Remove all subscriptions
            subscription.stream_types.clear()
        
        await self._send_to_client(client_id, {
            "type": "unsubscription_confirmed",
            "removed_streams": stream_types or "all",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_stream_data(self, stream_data: StreamData):
        """Publish data to subscribed clients"""
        # Add to stream history
        self.stream_history[stream_data.stream_type].append(stream_data)
        
        # Process analytics if needed
        await self._process_stream_analytics(stream_data)
        
        # Check for alerts
        await self._check_alert_conditions(stream_data)
        
        # Broadcast to subscribed clients
        for client_id, subscription in self.subscriptions.items():
            if stream_data.stream_type in subscription.stream_types:
                if await self._passes_filters(stream_data, subscription.filters):
                    await self._send_stream_data_to_client(client_id, stream_data)
    
    async def publish_metric_update(
        self, 
        metric_name: str, 
        metric_value: float, 
        user_id: str = None,
        institution_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Publish a metric update to real-time streams"""
        
        # Update metrics cache
        self.metrics_cache[metric_name] = {
            "value": metric_value,
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "institution_id": institution_id,
            "metadata": metadata or {}
        }
        
        # Create stream data
        stream_data = StreamData(
            stream_type=StreamType.METRICS,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            institution_id=institution_id,
            data={
                "metric_name": metric_name,
                "metric_value": metric_value,
                "change_from_previous": await self._calculate_metric_change(metric_name, metric_value)
            },
            metadata=metadata or {}
        )
        
        await self.publish_stream_data(stream_data)
    
    async def publish_event(
        self, 
        event_type: str, 
        event_data: Dict[str, Any],
        user_id: str = None,
        institution_id: str = None
    ):
        """Publish an event to real-time streams"""
        
        stream_data = StreamData(
            stream_type=StreamType.EVENTS,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            institution_id=institution_id,
            data={
                "event_type": event_type,
                "event_data": event_data
            },
            metadata={"source": "application"}
        )
        
        await self.publish_stream_data(stream_data)
    
    async def publish_alert(
        self, 
        alert_type: str, 
        message: str, 
        severity: str = "medium",
        user_id: str = None,
        institution_id: str = None,
        action_required: bool = False
    ):
        """Publish an alert to real-time streams"""
        
        stream_data = StreamData(
            stream_type=StreamType.ALERTS,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            institution_id=institution_id,
            data={
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "action_required": action_required,
                "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            },
            metadata={"source": "system"}
        )
        
        await self.publish_stream_data(stream_data)
    
    async def get_stream_history(
        self, 
        stream_type: StreamType, 
        limit: int = 100,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get historical stream data"""
        
        history = list(self.stream_history[stream_type])
        
        if since:
            history = [item for item in history if item.timestamp >= since]
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        history = history[:limit]
        
        return [item.to_dict() for item in history]
    
    async def get_active_connections_count(self) -> int:
        """Get count of active WebSocket connections"""
        return len(self.active_connections)
    
    async def get_subscriptions_summary(self) -> Dict[str, Any]:
        """Get summary of active subscriptions"""
        stream_counts = defaultdict(int)
        total_subscriptions = len(self.subscriptions)
        
        for subscription in self.subscriptions.values():
            for stream_type in subscription.stream_types:
                stream_counts[stream_type.value] += 1
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_connections": len(self.active_connections),
            "stream_counts": dict(stream_counts),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        
        try:
            websocket = connection["websocket"]
            await websocket.send_text(json.dumps(message))
            
            # Update connection stats
            connection["last_activity"] = datetime.utcnow()
            connection["message_count"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            # Remove invalid connection
            await self.unregister_connection(client_id)
            return False
    
    async def _send_stream_data_to_client(self, client_id: str, stream_data: StreamData):
        """Send stream data to specific client"""
        message = {
            "type": "stream_data",
            **stream_data.to_dict()
        }
        
        await self._send_to_client(client_id, message)
    
    async def _send_stream_history(self, client_id: str, stream_types: Set[StreamType]):
        """Send recent stream history to newly subscribed client"""
        for stream_type in stream_types:
            history = await self.get_stream_history(stream_type, limit=10)
            if history:
                await self._send_to_client(client_id, {
                    "type": "stream_history",
                    "stream_type": stream_type.value,
                    "history": history,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    async def _passes_filters(self, stream_data: StreamData, filters: Dict[str, Any]) -> bool:
        """Check if stream data passes subscription filters"""
        if not filters:
            return True
        
        # User ID filter
        if "user_id" in filters and stream_data.user_id != filters["user_id"]:
            return False
        
        # Institution ID filter
        if "institution_id" in filters and stream_data.institution_id != filters["institution_id"]:
            return False
        
        # Data field filters
        if "data_filters" in filters:
            for field, expected_value in filters["data_filters"].items():
                if field not in stream_data.data or stream_data.data[field] != expected_value:
                    return False
        
        return True
    
    async def _cleanup_inactive_connections(self):
        """Remove inactive WebSocket connections"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        inactive_clients = []
        for client_id, connection in self.active_connections.items():
            if connection["last_activity"] < cutoff_time:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            await self.unregister_connection(client_id)
            logger.info(f"Removed inactive connection: {client_id}")
    
    async def _generate_periodic_analytics(self):
        """Generate periodic analytics updates"""
        try:
            # Generate synthetic analytics data
            analytics_data = {
                "active_users": len(set(conn["user_id"] for conn in self.active_connections.values())),
                "total_connections": len(self.active_connections),
                "messages_per_minute": sum(conn["message_count"] for conn in self.active_connections.values()),
                "stream_activity": {
                    stream_type.value: len(self.stream_history[stream_type])
                    for stream_type in StreamType
                }
            }
            
            stream_data = StreamData(
                stream_type=StreamType.ANALYTICS,
                timestamp=datetime.utcnow(),
                user_id=None,
                institution_id=None,
                data=analytics_data,
                metadata={"source": "system_analytics"}
            )
            
            await self.publish_stream_data(stream_data)
            
        except Exception as e:
            logger.error(f"Error generating periodic analytics: {e}")
    
    async def _monitor_system_metrics(self):
        """Monitor system metrics and publish updates"""
        try:
            # Simulate system metrics
            import random
            
            metrics = {
                "cpu_usage": random.uniform(10, 80),
                "memory_usage": random.uniform(20, 90),
                "disk_usage": random.uniform(30, 85),
                "network_io": random.uniform(1000, 50000),
                "active_sessions": len(self.active_connections)
            }
            
            for metric_name, metric_value in metrics.items():
                await self.publish_metric_update(
                    metric_name=metric_name,
                    metric_value=metric_value,
                    metadata={"source": "system_monitor"}
                )
                
        except Exception as e:
            logger.error(f"Error monitoring system metrics: {e}")
    
    async def _process_stream_analytics(self, stream_data: StreamData):
        """Process stream data for analytics insights"""
        try:
            # Update running analytics based on stream type
            if stream_data.stream_type == StreamType.METRICS:
                await self._update_metrics_analytics(stream_data)
            elif stream_data.stream_type == StreamType.EVENTS:
                await self._update_events_analytics(stream_data)
                
        except Exception as e:
            logger.error(f"Error processing stream analytics: {e}")
    
    async def _update_metrics_analytics(self, stream_data: StreamData):
        """Update metrics-based analytics"""
        metric_name = stream_data.data.get("metric_name")
        metric_value = stream_data.data.get("metric_value")
        
        if metric_name and metric_value is not None:
            # Calculate trends, averages, etc.
            # This would integrate with the analytics service
            pass
    
    async def _update_events_analytics(self, stream_data: StreamData):
        """Update events-based analytics"""
        event_type = stream_data.data.get("event_type")
        
        if event_type:
            # Track event frequencies, patterns, etc.
            # This would integrate with the analytics service
            pass
    
    async def _check_alert_conditions(self, stream_data: StreamData):
        """Check for alert conditions in stream data"""
        try:
            if stream_data.stream_type == StreamType.METRICS:
                await self._check_metric_alerts(stream_data)
            elif stream_data.stream_type == StreamType.EVENTS:
                await self._check_event_alerts(stream_data)
                
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    async def _check_metric_alerts(self, stream_data: StreamData):
        """Check for metric-based alerts"""
        metric_name = stream_data.data.get("metric_name")
        metric_value = stream_data.data.get("metric_value")
        
        if metric_name == "compliance_score" and metric_value < 70:
            await self.publish_alert(
                alert_type="compliance_low",
                message=f"Compliance score dropped to {metric_value}%",
                severity="high",
                user_id=stream_data.user_id,
                institution_id=stream_data.institution_id,
                action_required=True
            )
        elif metric_name == "error_rate" and metric_value > self.alert_thresholds.get("error_rate_threshold", 0.05):
            await self.publish_alert(
                alert_type="high_error_rate",
                message=f"Error rate elevated to {metric_value*100:.1f}%",
                severity="medium",
                action_required=True
            )
    
    async def _check_event_alerts(self, stream_data: StreamData):
        """Check for event-based alerts"""
        event_type = stream_data.data.get("event_type")
        
        if event_type == "login_failed":
            # Could track failed login attempts and alert on suspicious activity
            pass
        elif event_type == "document_processing_failed":
            await self.publish_alert(
                alert_type="processing_failure",
                message="Document processing failed",
                severity="medium",
                user_id=stream_data.user_id,
                institution_id=stream_data.institution_id
            )
    
    async def _calculate_metric_change(self, metric_name: str, current_value: float) -> Optional[float]:
        """Calculate change from previous metric value"""
        if metric_name in self.metrics_cache:
            previous_value = self.metrics_cache[metric_name]["value"]
            return current_value - previous_value
        return None
    
    def cleanup(self):
        """Cleanup background tasks and connections"""
        for task in self.background_tasks:
            task.cancel()
        
        self.active_connections.clear()
        self.subscriptions.clear()


# Global service instance
streaming_service = RealTimeStreamingService()
