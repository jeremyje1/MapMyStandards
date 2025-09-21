"""
Webhook service for real-time event notifications to external systems.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import httpx
import hashlib
import hmac
import json
from enum import Enum
from pydantic import BaseModel, HttpUrl

from ..core.config import settings
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Session
from ..database import Base

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Supported webhook event types."""
    # Evidence events
    EVIDENCE_UPLOADED = "evidence.uploaded"
    EVIDENCE_PROCESSED = "evidence.processed"
    EVIDENCE_FAILED = "evidence.failed"
    
    # Standards events
    STANDARDS_MAPPED = "standards.mapped"
    STANDARDS_GAP_FOUND = "standards.gap_found"
    
    # Report events
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"
    
    # User events
    USER_CREATED = "user.created"
    USER_TRIAL_STARTED = "user.trial_started"
    USER_SUBSCRIBED = "user.subscribed"
    
    # Institution events
    INSTITUTION_CREATED = "institution.created"
    INSTITUTION_UPDATED = "institution.updated"
    
    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_SYNC_COMPLETED = "integration.sync_completed"


class WebhookConfig(Base):
    """Webhook configuration model."""
    __tablename__ = "webhook_configs"
    
    id = Column(String, primary_key=True)
    institution_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    secret = Column(String, nullable=True)  # For HMAC signing
    events = Column(JSON, nullable=False)  # List of subscribed events
    headers = Column(JSON, nullable=True)  # Custom headers to include
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds
    
    # Statistics
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    total_sent = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)


class WebhookDelivery(Base):
    """Webhook delivery history."""
    __tablename__ = "webhook_deliveries"
    
    id = Column(String, primary_key=True)
    webhook_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    error_message = Column(Text, nullable=True)


class WebhookPayload(BaseModel):
    """Standard webhook payload structure."""
    event: str
    timestamp: str
    webhook_id: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class WebhookService:
    """Service for managing and sending webhooks."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.active_webhooks: Dict[str, List[WebhookConfig]] = {}
        self._load_task = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.load_webhooks()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def load_webhooks(self):
        """Load active webhooks from database."""
        try:
            # Query active webhooks grouped by event type
            webhooks = await db.fetch_all(
                "SELECT * FROM webhook_configs WHERE active = true"
            )
            
            self.active_webhooks.clear()
            for webhook in webhooks:
                for event in webhook['events']:
                    if event not in self.active_webhooks:
                        self.active_webhooks[event] = []
                    self.active_webhooks[event].append(webhook)
            
            logger.info(f"Loaded {len(webhooks)} active webhooks")
        except Exception as e:
            logger.error(f"Error loading webhooks: {e}")
    
    async def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        institution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Trigger a webhook event."""
        try:
            # Get webhooks subscribed to this event
            webhooks = self.active_webhooks.get(event.value, [])
            
            # Filter by institution if provided
            if institution_id:
                webhooks = [w for w in webhooks if w['institution_id'] == institution_id]
            
            if not webhooks:
                logger.debug(f"No webhooks registered for event: {event}")
                return
            
            # Create tasks for all webhooks
            tasks = []
            for webhook in webhooks:
                payload = WebhookPayload(
                    event=event.value,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    webhook_id=webhook['id'],
                    data=data,
                    metadata=metadata
                )
                tasks.append(self._send_webhook(webhook, payload))
            
            # Send all webhooks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error triggering webhook event {event}: {e}")
    
    async def _send_webhook(self, webhook: Dict[str, Any], payload: WebhookPayload):
        """Send a single webhook with retry logic."""
        delivery_id = f"del_{datetime.now().timestamp()}"
        
        # Record delivery attempt
        await self._record_delivery(delivery_id, webhook['id'], payload)
        
        for attempt in range(webhook.get('max_retries', 3)):
            try:
                # Prepare headers
                headers = {
                    'Content-Type': 'application/json',
                    'X-Webhook-Event': payload.event,
                    'X-Webhook-ID': webhook['id'],
                    'X-Webhook-Timestamp': payload.timestamp,
                    'X-Webhook-Delivery': delivery_id
                }
                
                # Add custom headers
                if webhook.get('headers'):
                    headers.update(webhook['headers'])
                
                # Add HMAC signature if secret is configured
                payload_json = payload.json()
                if webhook.get('secret'):
                    signature = self._generate_signature(webhook['secret'], payload_json)
                    headers['X-Webhook-Signature'] = signature
                
                # Send request
                response = await self.client.post(
                    webhook['url'],
                    json=payload.dict(),
                    headers=headers
                )
                
                # Update statistics
                await self._update_webhook_stats(webhook['id'], success=response.is_success)
                
                # Record response
                await self._update_delivery(
                    delivery_id,
                    response.status_code,
                    response.text[:1000],  # Limit response body size
                    attempt + 1
                )
                
                if response.is_success:
                    logger.info(f"Webhook delivered successfully: {webhook['id']} -> {payload.event}")
                    return
                else:
                    logger.warning(f"Webhook failed with status {response.status_code}: {webhook['id']}")
                    
            except Exception as e:
                logger.error(f"Error sending webhook {webhook['id']}: {e}")
                await self._update_delivery(
                    delivery_id,
                    None,
                    str(e),
                    attempt + 1,
                    error=str(e)
                )
            
            # Wait before retry
            if attempt < webhook.get('max_retries', 3) - 1:
                await asyncio.sleep(webhook.get('retry_delay', 60))
        
        # All retries failed
        await self._update_webhook_stats(webhook['id'], success=False, error="Max retries exceeded")
    
    def _generate_signature(self, secret: str, payload: str) -> str:
        """Generate HMAC signature for webhook payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def _record_delivery(self, delivery_id: str, webhook_id: str, payload: WebhookPayload):
        """Record webhook delivery attempt."""
        try:
            await db.execute(
                """
                INSERT INTO webhook_deliveries (id, webhook_id, event_type, payload, created_at)
                VALUES (:id, :webhook_id, :event_type, :payload, :created_at)
                """,
                {
                    "id": delivery_id,
                    "webhook_id": webhook_id,
                    "event_type": payload.event,
                    "payload": payload.dict(),
                    "created_at": datetime.now(timezone.utc)
                }
            )
        except Exception as e:
            logger.error(f"Error recording webhook delivery: {e}")
    
    async def _update_delivery(
        self, 
        delivery_id: str, 
        status_code: Optional[int], 
        response_body: str,
        attempt_count: int,
        error: Optional[str] = None
    ):
        """Update webhook delivery record."""
        try:
            await db.execute(
                """
                UPDATE webhook_deliveries 
                SET response_status = :status,
                    response_body = :body,
                    attempt_count = :attempts,
                    error_message = :error,
                    delivered_at = :delivered_at
                WHERE id = :id
                """,
                {
                    "id": delivery_id,
                    "status": status_code,
                    "body": response_body,
                    "attempts": attempt_count,
                    "error": error,
                    "delivered_at": datetime.now(timezone.utc) if status_code and 200 <= status_code < 300 else None
                }
            )
        except Exception as e:
            logger.error(f"Error updating webhook delivery: {e}")
    
    async def _update_webhook_stats(self, webhook_id: str, success: bool, error: Optional[str] = None):
        """Update webhook statistics."""
        try:
            if success:
                await db.execute(
                    """
                    UPDATE webhook_configs
                    SET last_triggered_at = :now,
                        last_success_at = :now,
                        total_sent = total_sent + 1,
                        updated_at = :now
                    WHERE id = :id
                    """,
                    {"id": webhook_id, "now": datetime.now(timezone.utc)}
                )
            else:
                await db.execute(
                    """
                    UPDATE webhook_configs
                    SET last_triggered_at = :now,
                        last_error_at = :now,
                        last_error_message = :error,
                        total_sent = total_sent + 1,
                        total_failed = total_failed + 1,
                        updated_at = :now
                    WHERE id = :id
                    """,
                    {
                        "id": webhook_id,
                        "now": datetime.now(timezone.utc),
                        "error": error
                    }
                )
        except Exception as e:
            logger.error(f"Error updating webhook stats: {e}")
    
    async def create_webhook(
        self,
        institution_id: str,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a new webhook configuration."""
        webhook_id = f"wh_{datetime.now().timestamp()}"
        
        try:
            await db.execute(
                """
                INSERT INTO webhook_configs (
                    id, institution_id, url, secret, events, headers, 
                    active, created_at, updated_at
                )
                VALUES (
                    :id, :institution_id, :url, :secret, :events, :headers,
                    true, :now, :now
                )
                """,
                {
                    "id": webhook_id,
                    "institution_id": institution_id,
                    "url": url,
                    "secret": secret,
                    "events": [e.value for e in events],
                    "headers": headers,
                    "now": datetime.now(timezone.utc)
                }
            )
            
            # Reload webhooks
            await self.load_webhooks()
            
            return webhook_id
            
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise
    
    async def delete_webhook(self, webhook_id: str):
        """Delete a webhook configuration."""
        try:
            await db.execute(
                "UPDATE webhook_configs SET active = false WHERE id = :id",
                {"id": webhook_id}
            )
            
            # Reload webhooks
            await self.load_webhooks()
            
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            raise
    
    async def get_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history."""
        try:
            deliveries = await db.fetch_all(
                """
                SELECT * FROM webhook_deliveries
                WHERE webhook_id = :webhook_id
                ORDER BY created_at DESC
                LIMIT :limit
                """,
                {"webhook_id": webhook_id, "limit": limit}
            )
            return [dict(d) for d in deliveries]
            
        except Exception as e:
            logger.error(f"Error fetching webhook deliveries: {e}")
            return []


# Global webhook service instance
webhook_service = WebhookService()