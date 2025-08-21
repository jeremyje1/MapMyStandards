"""
Payment API Routes for A³E
Handles trial signup, subscription management, and billing
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi import APIRouter as _APIRouterAlias
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging
import os

try:
    from ...services.payment_service import PaymentService  # type: ignore
    _payment_service_available = True
except Exception as e:  # catch ImportError or dependency errors
    _payment_service_available = False
    _payment_service_import_error = e
from ...core.auth import verify_api_key
from ...core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Basic static pricing reference (can be expanded or sourced dynamically later)
PRICING: Dict[str, Dict[str, Any]] = {
    "college_monthly": {"interval": "month", "trial_days": 7},
    "college_yearly": {"interval": "year", "trial_days": 7},
    "multicampus_monthly": {"interval": "month", "trial_days": 7},
    "multicampus_yearly": {"interval": "year", "trial_days": 7},
}

# Pydantic Models
class TrialSignupRequest(BaseModel):
    institution_name: str
    email: EmailStr
    role: str
    plan: str = "college_monthly"  # Updated default to match stripe_trial_setup.md
    payment_method_id: str  # Stripe payment method ID
    phone: Optional[str] = None
    newsletter_opt_in: bool = False
    coupon_code: Optional[str] = None  # Added coupon support

class SubscriptionRequest(BaseModel):
    customer_id: str
    plan: str
    payment_method_id: str

class PaymentResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Lazy initialize payment service only when endpoint hit
_payment_service_instance: Optional[PaymentService] = None

def get_payment_service() -> PaymentService:
    """Dependency function to get / create payment service instance"""
    if not _payment_service_available:
        raise HTTPException(status_code=503, detail="Payment service unavailable on this deployment")
    global _payment_service_instance
    if _payment_service_instance is None:
        _payment_service_instance = PaymentService()  # type: ignore
    return _payment_service_instance

@router.post("/trial/signup")
async def trial_signup(request: TrialSignupRequest, payment_service: PaymentService = Depends(get_payment_service)):
    """
    Create a 7-day free trial subscription with automatic billing.
    Requires credit card for seamless conversion.
    """
    logger.info(f"Trial signup request received for email: {request.email}, plan: {request.plan}")
    try:
        # Create trial subscription with Stripe
        result = await payment_service.create_trial_subscription(
            email=request.email,
            plan=request.plan,
            payment_method_id=request.payment_method_id,
            coupon_code=request.coupon_code
        )
        
        if result['success']:
            return {
                "success": True,
                "message": "7-day free trial started successfully",
                "trial_id": result['subscription_id'],  # Add trial_id for frontend redirect
                "data": {
                    "api_key": result['api_key'],
                    "trial_end": result['trial_end'], 
                    "customer_id": result['customer_id'],
                    "subscription_id": result['subscription_id'],
                    "plan": request.plan,
                    "status": "trialing",
                    "billing_starts": result['trial_end']  # When billing begins
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trial signup error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # Check if this is a Stripe configuration issue
        if "API key" in str(e):
            raise HTTPException(
                status_code=503, 
                detail="Payment system is not properly configured. Please contact support."
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to create trial subscription: {str(e)}")

@router.post("/subscription/create", response_model=PaymentResponse)
async def create_subscription(
    request: SubscriptionRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a paid subscription"""
    try:
        result = await payment_service.create_subscription(
            customer_id=request.customer_id,
            plan=request.plan,
            payment_method_id=request.payment_method_id
        )
        
        return PaymentResponse(
            status="success",
            message="Subscription created successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/subscription/cancel")
async def cancel_subscription(
    customer_id: str,
    api_key: str = Depends(verify_api_key),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Cancel an active subscription"""
    try:
        result = await payment_service.cancel_subscription(customer_id)
        
        return PaymentResponse(
            status="success",
            message="Subscription cancelled successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Subscription cancellation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/account/status")
async def get_account_status(
    api_key: str = Depends(verify_api_key),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get current account status and usage"""
    try:
        result = await payment_service.get_account_status(api_key)
        
        return PaymentResponse(
            status="success",
            message="Account status retrieved",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Account status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/coupon/validate")
async def validate_coupon(coupon_code: str, payment_service: PaymentService = Depends(get_payment_service)):
    """Validate a coupon code"""
    try:
        result = await payment_service.validate_coupon(coupon_code.upper())
        
        return PaymentResponse(
            status="success" if result['valid'] else "error",
            message="Coupon validated" if result['valid'] else result.get('error', 'Invalid coupon'),
            data=result if result['valid'] else None
        )
        
    except Exception as e:
        logger.error(f"Coupon validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to validate coupon"
        )

@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans (matches stripe_trial_setup.md exactly)"""
    plans = {
        "college_monthly": {
            "name": "A³E College Plan",
            "price": 297.00,
            "currency": "USD",
            "interval": "month",
            "trial_days": 7,
            "description": "Complete accreditation automation for colleges and their accreditation teams",
            "features": [
                "Unlimited document analysis",
                "Up to 3 campus/department profiles", 
                "Full AI pipeline (4-agent system)",
                "Canvas LMS integration",
                "Comprehensive audit trails",
                "Monthly compliance reports",
                "Priority email support"
            ]
        },
        "college_yearly": {
            "name": "A³E College Plan (Annual)",
            "price": 2970.00,
            "currency": "USD", 
            "interval": "year",
            "trial_days": 7,
            "description": "Complete accreditation automation for colleges and their accreditation teams - Annual billing",
            "savings": "2 months free",
            "features": [
                "Everything in Monthly Plan",
                "2 months free (annual billing)",
                "Priority support queue"
            ]
        },
        "multicampus_monthly": {
            "name": "A³E Multi-Campus Plan",
            "price": 897.00,
            "currency": "USD",
            "interval": "month", 
            "trial_days": 7,
            "description": "Enterprise accreditation management for multi-campus colleges",
            "features": [
                "Everything in College Plan",
                "Unlimited campus/department profiles",
                "White-label option available",
                "API access (10K calls/month)",
                "Dedicated success manager",
                "Custom integrations",
                "Phone support"
            ]
        },
        "multicampus_yearly": {
            "name": "A³E Multi-Campus Plan (Annual)",
            "price": 8073.00,
            "currency": "USD",
            "interval": "year",
            "trial_days": 21,
            "description": "Enterprise accreditation management for multi-campus colleges - Annual billing",
            "savings": "2 months free",
            "features": [
                "Everything in Monthly Plan",
                "2 months free (annual billing)",
                "Priority implementation"
            ]
        }
    }
    
    return PaymentResponse(
        status="success",
        message="Pricing plans retrieved",
        data={"plans": plans}
    )

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment events"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # For development, accept webhooks without signature verification
        # In production, always verify with stripe.Webhook.construct_event
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if webhook_secret and sig_header:
            try:
                import stripe
                event = stripe.Webhook.construct_event(
                    body, sig_header, webhook_secret
                )
            except ValueError:
                logger.error("Invalid webhook payload")
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError:
                logger.error("Invalid webhook signature")
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            # Development mode - parse without verification
            import json
            event = json.loads(body)
            logger.warning("⚠️ Webhook signature not verified (dev mode)")
        
        event_type = event.get("type")
        logger.info(f"Processing webhook: {event_type}")
        
        # Handle checkout session completed
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            customer_email = session.get("customer_details", {}).get("email")
            if customer_email:
                # Log successful subscription
                logger.info(f"✅ New subscription: {customer_email}")
                # TODO: Update user subscription status in database
                
        elif event_type == "payment_intent.succeeded":
            # Handle successful payment
            payment = event["data"]["object"]
            logger.info(f"✅ Payment succeeded: {payment.get('id')}")
            
        elif event_type == "invoice.payment_failed":
            # Handle failed payment
            invoice = event["data"]["object"]
            logger.warning(f"⚠️ Payment failed for customer: {invoice.get('customer')}")
            
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            subscription = event["data"]["object"]
            logger.info(f"Subscription cancelled: {subscription.get('id')}")
        
        return {"status": "success", "type": event_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

# Legacy/alternate path handler (Stripe webhooks currently hitting /api/billing/webhook/stripe)
legacy_router = _APIRouterAlias(prefix="/api/billing", tags=["billing-legacy"])

@legacy_router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook_legacy(request: Request):
    return await stripe_webhook(request)

async def _handle_payment_success(payment_intent):
    """Handle successful payment"""
    customer_id = payment_intent.get("customer")
    # Update account status to active
    logger.info(f"Payment succeeded for customer {customer_id}")

async def _handle_payment_failure(invoice):
    """Handle failed payment"""
    customer_id = invoice.get("customer")
    # Send notification, retry payment, or suspend account
    logger.warning(f"Payment failed for customer {customer_id}")

async def _handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get("customer")
    # Update account status
    logger.info(f"Subscription cancelled for customer {customer_id}")


@router.get("/config/stripe-key", include_in_schema=False)
async def get_stripe_publishable_key():
    """Get Stripe publishable key for client-side initialization"""
    settings = get_settings()
    key = settings.STRIPE_PUBLISHABLE_KEY
    
    return {
        "publishable_key": key,
        "environment": "live" if key.startswith("pk_live") else "test"
    }

@router.get("/config/debug", include_in_schema=False)
async def debug_stripe_config():
    """Debug endpoint to check Stripe configuration"""
    settings = get_settings()
    import stripe
    
    return {
        "stripe_key_configured": bool(stripe.api_key),
        "stripe_key_length": len(stripe.api_key) if stripe.api_key else 0,
        "publishable_key_exists": bool(settings.STRIPE_PUBLISHABLE_KEY),
        "publishable_key_starts": settings.STRIPE_PUBLISHABLE_KEY[:10] if settings.STRIPE_PUBLISHABLE_KEY else None,
        "secret_key_exists": bool(settings.STRIPE_SECRET_KEY),
        "secret_key_length": len(settings.STRIPE_SECRET_KEY) if settings.STRIPE_SECRET_KEY else 0,
        "price_ids": {
            "college_monthly": settings.STRIPE_PRICE_COLLEGE_MONTHLY or "Not set",
            "college_yearly": settings.STRIPE_PRICE_COLLEGE_YEARLY or "Not set",
            "multicampus_monthly": settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY or "Not set",
            "multicampus_yearly": settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY or "Not set"
        }
    }
