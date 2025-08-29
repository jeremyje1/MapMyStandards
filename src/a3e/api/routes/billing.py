"""
Payment API Routes for A³E
Handles trial signup, subscription management, and billing
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
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
    role: Optional[str] = None  # Made optional since frontend might not send it
    plan: str = "college_monthly"  # Updated default to match stripe_trial_setup.md
    payment_method_id: str  # Stripe payment method ID
    first_name: Optional[str] = None  # Accept first_name from frontend
    last_name: Optional[str] = None  # Accept last_name from frontend
    phone: Optional[str] = None
    newsletter_opt_in: bool = False
    coupon_code: Optional[str] = None  # Added coupon support
    cardholder_name: Optional[str] = None  # Frontend sends this
    billing_email: Optional[str] = None  # Frontend sends this
    billing_address: Optional[str] = None  # Frontend sends this
    billing_zip: Optional[str] = None  # Frontend sends this
    user_count: Optional[str] = None  # Frontend might send this
    primary_accreditor: Optional[str] = None  # Frontend might send this

class SubscriptionRequest(BaseModel):
    customer_id: str
    plan: str
    payment_method_id: str

class CheckoutSessionRequest(BaseModel):
    price_id: str
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    trial_period_days: Optional[int] = 7
    success_url: str
    cancel_url: str

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
        try:
            import stripe  # local import for safety
            logger.info("[billing] PaymentService instantiated (stripe_key_present=%s)", bool(stripe.api_key))
        except Exception:
            pass
    return _payment_service_instance

@router.post("/trial/signup")
async def trial_signup(request: TrialSignupRequest, payment_service: PaymentService = Depends(get_payment_service)):
    """
    Create a 7-day free trial subscription with automatic billing.
    Requires credit card for seamless conversion.
    """
    logger.info(f"Trial signup request received for email: {request.email}, plan: {request.plan}")
    logger.info(f"Full request data: institution_name={request.institution_name}, role={request.role}, first_name={request.first_name}, last_name={request.last_name}")
    import time
    started = time.time()
    try:
        # Log Stripe key presence + short payment method id for diagnostics
        try:
            import stripe
            logger.info(
                "[trial] stripe_key_present=%s key_type=%s pm_prefix=%s plan=%s",
                bool(stripe.api_key),
                ('live' if stripe.api_key and str(stripe.api_key).startswith('sk_live') else 'test' if stripe.api_key and str(stripe.api_key).startswith('sk_test') else 'unset'),
                (request.payment_method_id[:8] + '...' if request.payment_method_id else None),
                request.plan
            )
        except Exception:
            logger.info("[trial] Unable to introspect Stripe module for diagnostics")
        # Create trial subscription with Stripe (timed)
        import asyncio
        stage = "create_trial_subscription"
        try:
            result = await asyncio.wait_for(
                payment_service.create_trial_subscription(
                    email=request.email,
                    plan=request.plan,
                    payment_method_id=request.payment_method_id,
                    coupon_code=request.coupon_code
                ),
                timeout=12
            )
        except asyncio.TimeoutError:
            elapsed = int((time.time() - started) * 1000)
            logger.error("Trial signup timed out after %sms (stage=%s)", elapsed, stage)
            if hasattr(payment_service, 'last_trial_failure'):
                setattr(payment_service, 'last_trial_failure', {
                    'stage': stage,
                    'elapsed_ms': elapsed,
                    'email': request.email,
                    'plan': request.plan,
                    'timeout_sec': 12
                })
            raise HTTPException(status_code=504, detail={"error": "Signup timed out", "stage": stage, "elapsed_ms": elapsed})

        if result['success']:
            elapsed_total = int((time.time() - started) * 1000)
            result.setdefault('timing_ms', elapsed_total)
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
            # Enhanced diagnostics for 400 errors seen in client
            logger.error(
                "Trial signup failed (email=%s plan=%s payment_method_id=%s) -> %s",
                request.email,
                request.plan,
                request.payment_method_id[:10] + '...' if request.payment_method_id else None,
                result
            )
            # Provide a structured error so frontend can surface stage
            error_payload = {"error": result.get('error', 'Unknown error'), "stage": result.get('stage')}
            raise HTTPException(status_code=400, detail=error_payload)
            
    except HTTPException:
        raise
    except Exception as e:
        elapsed_total = int((time.time() - started) * 1000)
        logger.error(f"Trial signup error after {elapsed_total}ms: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")

        # Check if this is a Stripe configuration issue
        if "API key" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Payment system is not properly configured. Please contact support."
            )

        raise HTTPException(status_code=500, detail={"error": f"Failed to create trial subscription: {str(e)}", "elapsed_ms": elapsed_total})

@router.get("/trial/ping", include_in_schema=False)
async def trial_ping():
    """Lightweight latency/availability probe for signup flow debugging."""
    import time
    import uuid
    return {"ok": True, "ts": time.time(), "id": str(uuid.uuid4())}

@router.get("/trial/last-failure", include_in_schema=False)
async def trial_last_failure(payment_service: PaymentService = Depends(get_payment_service)):
    """Return (and preserve) the last in-memory trial signup failure details for debugging."""
    failure = getattr(payment_service, 'last_trial_failure', None)
    return {"failure": failure}

@router.get("/trial/diagnose", include_in_schema=False)
async def trial_diagnose(payment_service: PaymentService = Depends(get_payment_service)):
    """Expose current plan->price resolution & stripe key presence for debugging.

    Hardened to always return JSON (never bare 500 plain text) with an 'ok' flag.
    """
    import time
    started = time.time()
    try:
        settings = get_settings()
        import stripe
        plans = [
            'college', 'college_monthly', 'college_yearly', 'multicampus', 'multicampus_monthly', 'multicampus_yearly'
        ]
        price_map = {}
        for p in plans:
            try:
                price_map[p] = payment_service._get_price_id(p)  # type: ignore (debug only)
            except Exception as e:  # pragma: no cover - defensive
                price_map[p] = f"error: {e}"  # noqa: E501
        import stripe as _s  # alias for reuse
        resp = {
            'ok': True,
            'stripe_key_present': bool(_s.api_key),
            'stripe_key_type': 'live' if _s.api_key and _s.api_key.startswith('sk_live') else ('test' if _s.api_key and _s.api_key.startswith('sk_test') else 'unset'),
            'plans': price_map,
            'env_prices': {
                'STRIPE_PRICE_COLLEGE_MONTHLY': settings.STRIPE_PRICE_COLLEGE_MONTHLY,
                'STRIPE_PRICE_COLLEGE_YEARLY': settings.STRIPE_PRICE_COLLEGE_YEARLY,
                'STRIPE_PRICE_MULTI_CAMPUS_MONTHLY': settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY,
                'STRIPE_PRICE_MULTI_CAMPUS_YEARLY': settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY
            },
            'last_failure': getattr(payment_service, 'last_trial_failure', None),
            'elapsed_ms': int((time.time() - started) * 1000)
        }
        return resp
    except Exception as e:  # pragma: no cover - diagnostic path
        logger.exception("trial_diagnose failure")
        return JSONResponse(status_code=500, content={
            'ok': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'elapsed_ms': int((time.time() - started) * 1000)
        })

@router.get("/trial/verify-prices", include_in_schema=False)
async def trial_verify_prices(payment_service: PaymentService = Depends(get_payment_service)):
    """Retrieve each configured price from Stripe to confirm it exists under current key."""
    import stripe
    plans = ['college_monthly', 'college_yearly', 'multicampus_monthly', 'multicampus_yearly']
    results = {}
    for p in plans:
        pid = payment_service._get_price_id(p)  # type: ignore
        if not pid:
            results[p] = {'price_id': None, 'exists': False, 'error': 'missing_price_id'}
            continue
        try:
            price_obj = stripe.Price.retrieve(pid)
            results[p] = {
                'price_id': pid,
                'exists': True,
                'currency': getattr(price_obj, 'currency', None),
                'unit_amount': getattr(price_obj, 'unit_amount', None),
                'recurring': getattr(price_obj, 'recurring', None),
                'livemode': getattr(price_obj, 'livemode', None)
            }
        except stripe.error.InvalidRequestError as e:
            results[p] = {'price_id': pid, 'exists': False, 'error': str(e)}
        except Exception as e:  # pragma: no cover
            results[p] = {'price_id': pid, 'exists': False, 'error': f'unexpected: {e}'}
    return {'verification': results}

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


@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """Create a Stripe Checkout session for professional checkout experience"""
    try:
        import stripe
        
        # Build checkout session parameters
        session_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': request.price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': request.success_url,
            'cancel_url': request.cancel_url,
            'billing_address_collection': 'required',
            'customer_creation': 'always',
            'allow_promotion_codes': True,
        }
        
        # Add trial period if specified
        if request.trial_period_days and request.trial_period_days > 0:
            session_params['subscription_data'] = {
                'trial_period_days': request.trial_period_days
            }
        
        # Add customer email if provided
        if request.customer_email:
            session_params['customer_email'] = request.customer_email
        
        # Add metadata if provided
        if request.metadata:
            session_params.setdefault('subscription_data', {})['metadata'] = request.metadata
        
        # Create the checkout session
        session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created checkout session {session.id} for price {request.price_id}")
        
        return {
            "id": session.id,
            "url": session.url
        }
        
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": f"Failed to create checkout session: {str(e)}"}
        )

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
