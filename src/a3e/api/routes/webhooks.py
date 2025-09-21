"""
API routes for webhook management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, HttpUrl
import logging
from datetime import datetime, timezone

from ...services.webhook_service import webhook_service, WebhookEvent
from ...core.auth import get_current_user
from ...models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class CreateWebhookRequest(BaseModel):
    """Request model for creating a webhook."""
    url: HttpUrl
    events: List[WebhookEvent]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class UpdateWebhookRequest(BaseModel):
    """Request model for updating a webhook."""
    url: Optional[HttpUrl] = None
    events: Optional[List[WebhookEvent]] = None
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Response model for webhook data."""
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    last_triggered_at: Optional[str] = None
    last_success_at: Optional[str] = None
    total_sent: int
    total_failed: int


@router.get("/")
async def list_webhooks(
    current_user: User = Depends(get_current_user)
) -> List[WebhookResponse]:
    """List all webhooks for the current user's institution."""
    try:
        # Get webhooks for the user's institution
        from ...models import db
        webhooks = await db.fetch_all(
            """
            SELECT id, url, events, active, created_at, 
                   last_triggered_at, last_success_at, total_sent, total_failed
            FROM webhook_configs
            WHERE institution_id = :institution_id
            ORDER BY created_at DESC
            """,
            {"institution_id": current_user.institution_id}
        )
        
        return [
            WebhookResponse(
                id=w['id'],
                url=w['url'],
                events=w['events'],
                active=w['active'],
                created_at=w['created_at'].isoformat(),
                last_triggered_at=w['last_triggered_at'].isoformat() if w['last_triggered_at'] else None,
                last_success_at=w['last_success_at'].isoformat() if w['last_success_at'] else None,
                total_sent=w['total_sent'],
                total_failed=w['total_failed']
            )
            for w in webhooks
        ]
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list webhooks")


@router.post("/", response_model=Dict[str, str])
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Create a new webhook."""
    try:
        async with webhook_service:
            webhook_id = await webhook_service.create_webhook(
                institution_id=current_user.institution_id,
                url=str(request.url),
                events=request.events,
                secret=request.secret,
                headers=request.headers
            )
            
            # Test the webhook with a ping event
            await webhook_service.trigger_event(
                event=WebhookEvent.INTEGRATION_CONNECTED,
                data={
                    "message": "Webhook successfully configured",
                    "webhook_id": webhook_id,
                    "events": [e.value for e in request.events]
                },
                institution_id=current_user.institution_id,
                metadata={"test": True}
            )
            
            return {
                "message": "Webhook created successfully",
                "webhook_id": webhook_id,
                "status": "active"
            }
            
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get webhook details."""
    try:
        from ...models import db
        webhook = await db.fetch_one(
            """
            SELECT * FROM webhook_configs
            WHERE id = :id AND institution_id = :institution_id
            """,
            {"id": webhook_id, "institution_id": current_user.institution_id}
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return dict(webhook)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook")


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update a webhook configuration."""
    try:
        from ...models import db
        from datetime import datetime, timezone
        
        # Build update query dynamically
        update_fields = []
        params = {"id": webhook_id, "institution_id": current_user.institution_id}
        
        if request.url is not None:
            update_fields.append("url = :url")
            params["url"] = str(request.url)
        
        if request.events is not None:
            update_fields.append("events = :events")
            params["events"] = [e.value for e in request.events]
        
        if request.secret is not None:
            update_fields.append("secret = :secret")
            params["secret"] = request.secret
        
        if request.headers is not None:
            update_fields.append("headers = :headers")
            params["headers"] = request.headers
        
        if request.active is not None:
            update_fields.append("active = :active")
            params["active"] = request.active
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = :updated_at")
        params["updated_at"] = datetime.now(timezone.utc)
        
        query = f"""
            UPDATE webhook_configs
            SET {', '.join(update_fields)}
            WHERE id = :id AND institution_id = :institution_id
        """
        
        result = await db.execute(query, params)
        
        if result == 0:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Reload webhooks
        async with webhook_service:
            await webhook_service.load_webhooks()
        
        return {"message": "Webhook updated successfully", "webhook_id": webhook_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to update webhook")


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a webhook."""
    try:
        # Verify ownership
        from ...models import db
        webhook = await db.fetch_one(
            """
            SELECT id FROM webhook_configs
            WHERE id = :id AND institution_id = :institution_id
            """,
            {"id": webhook_id, "institution_id": current_user.institution_id}
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        async with webhook_service:
            await webhook_service.delete_webhook(webhook_id)
        
        return {"message": "Webhook deleted successfully", "webhook_id": webhook_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete webhook")


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get webhook delivery history."""
    try:
        # Verify ownership
        from ...models import db
        webhook = await db.fetch_one(
            """
            SELECT id FROM webhook_configs
            WHERE id = :id AND institution_id = :institution_id
            """,
            {"id": webhook_id, "institution_id": current_user.institution_id}
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        async with webhook_service:
            deliveries = await webhook_service.get_webhook_deliveries(webhook_id, limit)
        
        return deliveries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook deliveries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get delivery history")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Send a test event to the webhook."""
    try:
        # Verify ownership
        from ...models import db
        webhook = await db.fetch_one(
            """
            SELECT * FROM webhook_configs
            WHERE id = :id AND institution_id = :institution_id
            """,
            {"id": webhook_id, "institution_id": current_user.institution_id}
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        if not webhook['active']:
            raise HTTPException(status_code=400, detail="Webhook is not active")
        
        # Send test event
        async with webhook_service:
            await webhook_service.trigger_event(
                event=WebhookEvent.INTEGRATION_CONNECTED,
                data={
                    "message": "This is a test webhook event",
                    "webhook_id": webhook_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                institution_id=current_user.institution_id,
                metadata={"test": True}
            )
        
        return {
            "message": "Test event sent successfully",
            "webhook_id": webhook_id,
            "event": WebhookEvent.INTEGRATION_CONNECTED.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test event")


@router.get("/events/available")
async def get_available_events() -> List[Dict[str, str]]:
    """Get list of available webhook events."""
    return [
        {
            "event": event.value,
            "category": event.value.split('.')[0],
            "description": get_event_description(event)
        }
        for event in WebhookEvent
    ]


def get_event_description(event: WebhookEvent) -> str:
    """Get human-readable description for webhook event."""
    descriptions = {
        WebhookEvent.EVIDENCE_UPLOADED: "Triggered when evidence is uploaded",
        WebhookEvent.EVIDENCE_PROCESSED: "Triggered when evidence processing is complete",
        WebhookEvent.EVIDENCE_FAILED: "Triggered when evidence processing fails",
        WebhookEvent.STANDARDS_MAPPED: "Triggered when standards are mapped to evidence",
        WebhookEvent.STANDARDS_GAP_FOUND: "Triggered when a gap is found in standards compliance",
        WebhookEvent.REPORT_GENERATED: "Triggered when a report is generated",
        WebhookEvent.REPORT_EXPORTED: "Triggered when a report is exported",
        WebhookEvent.USER_CREATED: "Triggered when a new user is created",
        WebhookEvent.USER_TRIAL_STARTED: "Triggered when a user starts a trial",
        WebhookEvent.USER_SUBSCRIBED: "Triggered when a user subscribes",
        WebhookEvent.INSTITUTION_CREATED: "Triggered when an institution is created",
        WebhookEvent.INSTITUTION_UPDATED: "Triggered when an institution is updated",
        WebhookEvent.INTEGRATION_CONNECTED: "Triggered when an integration is connected",
        WebhookEvent.INTEGRATION_DISCONNECTED: "Triggered when an integration is disconnected",
        WebhookEvent.INTEGRATION_SYNC_COMPLETED: "Triggered when integration sync completes"
    }
    return descriptions.get(event, event.value)