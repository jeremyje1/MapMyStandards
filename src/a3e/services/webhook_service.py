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
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.config import settings

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Supported webhook event types."""
    # Evidence events
    EVIDENCE_UPLOADED = "evidence.uploaded"
    EVIDENCE_PROCESSED = "evidence.processed"
    EVIDENCE_FAILED = "evidence.failed"
    EVIDENCE_APPROVED = "evidence.approved"
    EVIDENCE_REJECTED = "evidence.rejected"
    
    # Standard events
    STANDARD_UPDATE = "standard.update"
    STANDARD_ADDED = "standard.added"
    STANDARD_REMOVED = "standard.removed"
    STANDARD_MAPPING_COMPLETE = "standard.mapping_complete"
    
    # Compliance events
    COMPLIANCE_CHECK_COMPLETE = "compliance.check_complete"
    COMPLIANCE_ISSUE_FOUND = "compliance.issue_found"
    COMPLIANCE_RESOLVED = "compliance.resolved"
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_UPDATED = "user.updated"
    
    # Organization events
    ORGANIZATION_UPDATED = "organization.updated"
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"


class WebhookService:
    """Service for managing webhooks and triggering events."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": "MapMyStandards-Webhook/1.0"
            }
        )
    
    async def trigger_webhook(
        self, 
        db: Session,
        event: WebhookEvent, 
        data: Dict[str, Any],
        institution_id: Optional[str] = None
    ) -> List[str]:
        """
        Trigger webhooks for a specific event.
        
        Args:
            db: Database session
            event: The webhook event type
            data: The event data payload
            institution_id: Optional institution ID to filter webhooks
        
        Returns:
            List of webhook IDs that were triggered
        """
        try:
            # Get active webhooks for this event
            query = text("""
                SELECT id, url, secret, headers
                FROM webhook_configs
                WHERE active = true
                AND :event = ANY(events)
                AND (institution_id IS NULL OR institution_id = :institution_id)
            """)
            
            result = db.execute(
                query,
                {"event": event, "institution_id": institution_id}
            )
            webhooks = result.fetchall()
            
            if not webhooks:
                logger.debug(f"No active webhooks found for event {event}")
                return []
            
            # Prepare the payload
            payload = {
                "event": event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            
            # Trigger webhooks concurrently
            tasks = []
            for webhook in webhooks:
                task = self._deliver_webhook(
                    db=db,
                    webhook_id=webhook.id,
                    url=webhook.url,
                    secret=webhook.secret,
                    headers=webhook.headers or {},
                    payload=payload
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            return [w.id for w in webhooks]
            
        except Exception as e:
            logger.error(f"Error triggering webhooks: {e}")
            return []
    
    async def _deliver_webhook(
        self,
        db: Session,
        webhook_id: str,
        url: str,
        secret: Optional[str],
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> bool:
        """Deliver a webhook with retry logic."""
        delivery_id = str(uuid.uuid4())
        
        # Create delivery record
        create_query = text("""
            INSERT INTO webhook_deliveries (
                id, webhook_id, event, payload, 
                status, created_at
            ) VALUES (
                :id, :webhook_id, :event, :payload,
                'pending', :created_at
            )
        """)
        
        db.execute(
            create_query,
            {
                "id": delivery_id,
                "webhook_id": webhook_id,
                "event": payload["event"],
                "payload": json.dumps(payload),
                "created_at": datetime.now(timezone.utc)
            }
        )
        db.commit()
        
        # Prepare headers
        request_headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": payload["event"],
            "X-Webhook-Delivery": delivery_id,
            **headers
        }
        
        # Add signature if secret is provided
        if secret:
            signature = self._generate_signature(secret, payload)
            request_headers["X-Webhook-Signature"] = signature
        
        # Attempt delivery with retries
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    url,
                    json=payload,
                    headers=request_headers
                )
                
                # Update delivery record with success
                update_query = text("""
                    UPDATE webhook_deliveries
                    SET status = 'delivered',
                        response_status = :status,
                        response_headers = :headers,
                        response_body = :body,
                        delivered_at = :delivered_at,
                        attempts = :attempts
                    WHERE id = :id
                """)
                
                db.execute(
                    update_query,
                    {
                        "id": delivery_id,
                        "status": response.status_code,
                        "headers": json.dumps(dict(response.headers)),
                        "body": response.text[:1000],  # Limit response body size
                        "delivered_at": datetime.now(timezone.utc),
                        "attempts": attempt + 1
                    }
                )
                
                # Update webhook last triggered
                webhook_update_query = text("""
                    UPDATE webhook_configs
                    SET last_triggered_at = :triggered_at
                    WHERE id = :id
                """)
                
                db.execute(
                    webhook_update_query,
                    {
                        "id": webhook_id,
                        "triggered_at": datetime.now(timezone.utc)
                    }
                )
                db.commit()
                
                return True
                
            except Exception as e:
                logger.warning(f"Webhook delivery attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries - 1:
                    # Final attempt failed
                    failure_query = text("""
                        UPDATE webhook_deliveries
                        SET status = 'failed',
                            error_message = :error,
                            attempts = :attempts
                        WHERE id = :id
                    """)
                    
                    db.execute(
                        failure_query,
                        {
                            "id": delivery_id,
                            "error": str(e),
                            "attempts": attempt + 1
                        }
                    )
                    
                    # Update webhook failure count
                    webhook_fail_query = text("""
                        UPDATE webhook_configs
                        SET failure_count = failure_count + 1,
                            last_failure_at = :failure_at
                        WHERE id = :id
                    """)
                    
                    db.execute(
                        webhook_fail_query,
                        {
                            "id": webhook_id,
                            "failure_at": datetime.now(timezone.utc)
                        }
                    )
                    db.commit()
                    
                    return False
                
                # Wait before retry
                await asyncio.sleep(retry_delay * (attempt + 1))
    
    def _generate_signature(self, secret: str, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def create_webhook(
        self,
        db: Session,
        name: str,
        url: str,
        events: List[str],
        institution_id: Optional[str] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        active: bool = True
    ) -> str:
        """Create a new webhook configuration."""
        webhook_id = str(uuid.uuid4())
        
        if not secret:
            secret = self._generate_secret()
        
        query = text("""
            INSERT INTO webhook_configs (
                id, name, url, events, secret, headers,
                institution_id, active, created_at, failure_count
            ) VALUES (
                :id, :name, :url, :events, :secret, :headers,
                :institution_id, :active, :created_at, 0
            )
        """)
        
        db.execute(
            query,
            {
                "id": webhook_id,
                "name": name,
                "url": url,
                "events": events,
                "secret": secret,
                "headers": json.dumps(headers) if headers else None,
                "institution_id": institution_id,
                "active": active,
                "created_at": datetime.now(timezone.utc)
            }
        )
        db.commit()
        
        return webhook_id
    
    def _generate_secret(self) -> str:
        """Generate a random webhook secret."""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    
    def delete_webhook(self, db: Session, webhook_id: str) -> bool:
        """Delete (deactivate) a webhook."""
        query = text("""
            UPDATE webhook_configs
            SET active = false
            WHERE id = :id
        """)
        
        result = db.execute(query, {"id": webhook_id})
        db.commit()
        
        return result.rowcount > 0
    
    def get_webhook_deliveries(
        self,
        db: Session,
        webhook_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent deliveries for a webhook."""
        query = text("""
            SELECT id, event, status, response_status,
                   created_at, delivered_at, attempts,
                   error_message
            FROM webhook_deliveries
            WHERE webhook_id = :webhook_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(
            query,
            {"webhook_id": webhook_id, "limit": limit}
        )
        
        deliveries = []
        for row in result:
            deliveries.append({
                "id": row.id,
                "event": row.event,
                "status": row.status,
                "response_status": row.response_status,
                "created_at": row.created_at,
                "delivered_at": row.delivered_at,
                "attempts": row.attempts,
                "error_message": row.error_message
            })
        
        return deliveries


# Create a global instance
webhook_service = WebhookService()