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
            customer_name = session.get("customer_details", {}).get("name", "Customer")
            stripe_customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            amount_total = session.get("amount_total", 0) / 100  # Convert cents to dollars
            
            # Determine plan name from metadata or line items
            metadata = session.get("metadata", {})
            plan_name = metadata.get("plan_name", "Professional")
            
            if customer_email:
                # Log successful subscription
                logger.info(f"✅ New subscription: {customer_email} - {plan_name} Plan")
                
                # Send welcome email to customer
                try:
                    from ...services.email_service import email_service
                    
                    # Extract customer name if available
                    customer_name = session.get("customer_details", {}).get("name", "Valued Customer")
                    
                    # Send welcome email
                    email_sent = email_service.send_welcome_email(
                        user_email=customer_email,
                        user_name=customer_name,
                        plan_name=plan_name
                    )
                    
                    if email_sent:
                        logger.info(f"✅ Welcome email sent to {customer_email}")
                    else:
                        logger.warning(f"⚠️ Failed to send welcome email to {customer_email}")
                    
                    # Send admin notification
                    admin_notification = email_service.send_admin_new_signup_notification(
                        user_email=customer_email,
                        user_name=customer_name,
                        institution=metadata.get("institution_name"),
                        trial=False,
                        plan_name=plan_name,
                        amount=amount_total,
                        stripe_customer_id=stripe_customer_id,
                        subscription_id=subscription_id
                    )
                    
                    if admin_notification:
                        logger.info(f"✅ Admin notification sent for new subscription: {customer_email}")
                    
                except Exception as e:
                    logger.error(f"Error sending emails for checkout completion: {e}")
                
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
        
        # Initialize Stripe API key
        settings = get_settings()
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key not configured")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
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

@router.get("/verify-session/{session_id}")
async def verify_checkout_session(session_id: str):
    """Verify a Stripe checkout session and return customer details"""
    try:
        import stripe
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Retrieve the checkout session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        return {
            "success": True,
            "customer_email": session.customer_details.email if session.customer_details else None,
            "customer_id": session.customer,
            "subscription_id": session.subscription,
            "payment_status": session.payment_status
        }
        
    except Exception as e:
        logger.error(f"Failed to verify checkout session {session_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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

@router.get("/debug/database", include_in_schema=False)
async def debug_database_schema():
    """Debug endpoint to check database schema and tables"""
    try:
        import asyncpg
        import os
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"error": "DATABASE_URL not found"}
            
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        table_list = [{"name": t['table_name'], "type": t['table_type']} for t in tables]
        
        # Check users table schema if it exists
        users_schema = None
        user_count = 0
        
        users_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        if users_exists:
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            users_schema = [
                {
                    "column": c['column_name'],
                    "type": c['data_type'],
                    "nullable": c['is_nullable'] == 'YES',
                    "default": c['column_default']
                } for c in columns
            ]
            
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users;")
        
        # Check institutions table
        institutions_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'institutions'
            );
        """)
        
        institution_count = 0
        if institutions_exists:
            institution_count = await conn.fetchval("SELECT COUNT(*) FROM institutions;")
        
        await conn.close()
        
        return {
            "database_url_configured": bool(database_url),
            "database_url_start": database_url[:30] if database_url else None,
            "total_tables": len(table_list),
            "tables": table_list,
            "users_table_exists": users_exists,
            "users_schema": users_schema,
            "user_count": user_count,
            "institutions_table_exists": institutions_exists,
            "institution_count": institution_count
        }
        
    except Exception as e:
        logger.error(f"Database debug error: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@router.post("/debug/migrate-users", include_in_schema=False)
async def migrate_users_table():
    """Migration endpoint to add authentication fields to users table"""
    try:
        import asyncpg
        import os
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"error": "DATABASE_URL not found"}
            
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        migration_sql = """
        BEGIN;

        -- Add authentication fields
        ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

        -- Add organization info fields  
        ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_name VARCHAR(255);
        ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_type VARCHAR(50);

        -- Add trial and subscription info
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT TRUE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50);
        ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
        ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);

        -- Add API access fields
        ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);
        ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_created_at TIMESTAMP;

        -- Add additional account status fields
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

        -- Add usage tracking fields
        ALTER TABLE users ADD COLUMN IF NOT EXISTS documents_analyzed INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS reports_generated INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS compliance_checks_run INTEGER DEFAULT 0;

        COMMIT;
        """
        
        # Execute migration in a transaction
        await conn.execute(migration_sql)
        
        # Create unique indexes separately (not in transaction to avoid conflicts)
        try:
            await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_customer_id 
                ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
            """)
            await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_subscription_id 
                ON users(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
            """)
            await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_api_key 
                ON users(api_key) WHERE api_key IS NOT NULL;
            """)
        except Exception as idx_error:
            logger.warning(f"Index creation warning (may already exist): {idx_error}")
        
        # Verify migration by checking new columns
        columns_after = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        await conn.close()
        
        return {
            "success": True,
            "message": "Migration completed successfully",
            "columns_after_migration": [
                {
                    "column": c['column_name'],
                    "type": c['data_type'],
                    "nullable": c['is_nullable'] == 'YES',
                    "default": c['column_default']
                } for c in columns_after
            ]
        }
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return {"success": False, "error": str(e), "error_type": type(e).__name__}

@router.post("/debug/seed-comprehensive-standards", include_in_schema=False)
async def seed_comprehensive_standards():
    """Seed the database with comprehensive US accreditation standards"""
    try:
        import asyncpg
        import os
        from datetime import datetime
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"error": "DATABASE_URL not found"}
            
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Comprehensive US Accreditation Standards
        standards_data = [
            # ===== SACSCOC STANDARDS (Southern) =====
            {
                "standard_id": "SACSCOC_1_1",
                "accreditor_id": "sacscoc",
                "title": "Mission",
                "description": "The institution has a clearly defined mission statement that articulates the institution's purpose, student population served, and commitment to student learning and student achievement.",
                "category": "Institutional Mission and Effectiveness",
                "subcategory": "Mission Statement",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Board Approval Documentation", "Strategic Plan"]
            },
            {
                "standard_id": "SACSCOC_2_1", 
                "accreditor_id": "sacscoc",
                "title": "Degree Standards",
                "description": "The institution offers one or more degree programs based on at least 60 semester credit hours or the equivalent at the baccalaureate level; at least 30 semester credit hours or the equivalent at the master's level.",
                "category": "Academic and Student Affairs",
                "subcategory": "Degree Requirements",
                "version": "2024",
                "effective_date": "2024-01-01", 
                "is_required": True,
                "evidence_requirements": ["Degree Program Documentation", "Credit Hour Requirements", "Catalog Pages"]
            },
            {
                "standard_id": "SACSCOC_8_1",
                "accreditor_id": "sacscoc",
                "title": "Faculty",
                "description": "The institution employs a sufficient number of qualified faculty to support the mission of the institution and the goals of the degree programs.",
                "category": "Faculty",
                "subcategory": "Faculty Qualifications",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Faculty CVs", "Qualification Matrix", "Teaching Load Documentation"]
            },
            {
                "standard_id": "SACSCOC_QEP",
                "accreditor_id": "sacscoc",
                "title": "Quality Enhancement Plan (QEP)",
                "description": "The institution develops and implements a Quality Enhancement Plan (QEP) that demonstrates institutional capability for the initiation, implementation, and completion of the QEP.",
                "category": "Quality Enhancement",
                "subcategory": "QEP Implementation",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["QEP Document", "Implementation Timeline", "Assessment Plan", "Resource Allocation"]
            },
            {
                "standard_id": "SACSCOC_SUBST_CHANGE",
                "accreditor_id": "sacscoc",
                "title": "Substantive Change",
                "description": "The institution reports substantive changes to SACSCOC in accordance with the substantive change policy and, when required, obtains approval prior to implementation.",
                "category": "Compliance",
                "subcategory": "Substantive Change",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Substantive Change Notifications", "Approval Documentation", "Implementation Plans"]
            },
            
            # ===== NECHE STANDARDS (New England) =====
            {
                "standard_id": "NECHE_1",
                "accreditor_id": "neche",
                "title": "Mission and Purposes",
                "description": "The institution's mission and purposes are appropriate to higher education, clearly stated, and consistently implemented throughout the institution.",
                "category": "Mission and Purposes",
                "subcategory": "Institutional Mission",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Strategic Planning Documents", "Board Minutes"]
            },
            {
                "standard_id": "NECHE_2",
                "accreditor_id": "neche",
                "title": "Planning and Evaluation",
                "description": "The institution undertakes planning and evaluation to accomplish and improve the achievement of its mission and purposes.",
                "category": "Planning and Evaluation",
                "subcategory": "Strategic Planning",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Strategic Plan", "Assessment Reports", "Planning Process Documentation"]
            },
            {
                "standard_id": "NECHE_4",
                "accreditor_id": "neche",
                "title": "Academic Program",
                "description": "The institution's academic programs are appropriate to higher education, support the institution's mission, and are characterized by rigor and coherence.",
                "category": "Academic Programs",
                "subcategory": "Program Quality",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Program Descriptions", "Curriculum Maps", "Learning Outcomes Assessment"]
            },
            
            # ===== MSCHE STANDARDS (Middle States) =====
            {
                "standard_id": "MSCHE_I",
                "accreditor_id": "msche",
                "title": "Mission and Goals",
                "description": "The institution's mission defines its purpose within the context of higher education, the students it serves, and what it intends to accomplish.",
                "category": "Mission and Goals",
                "subcategory": "Institutional Identity",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Goals Documentation", "Assessment Evidence"]
            },
            {
                "standard_id": "MSCHE_II",
                "accreditor_id": "msche",
                "title": "Ethics and Integrity",
                "description": "Ethics and integrity are central, indispensable, and defining hallmarks of effective higher education institutions.",
                "category": "Ethics and Integrity",
                "subcategory": "Institutional Ethics",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Ethics Policies", "Integrity Documentation", "Compliance Records"]
            },
            {
                "standard_id": "MSCHE_III",
                "accreditor_id": "msche",
                "title": "Design and Delivery of the Student Learning Experience",
                "description": "The institution provides students with learning experiences that are characterized by rigor and coherence at all program, certificate, and degree levels.",
                "category": "Student Learning",
                "subcategory": "Learning Experience Design",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Curriculum Design", "Learning Assessment", "Program Reviews"]
            },
            
            # ===== WASC STANDARDS (Western) =====
            {
                "standard_id": "WASC_1",
                "accreditor_id": "wasc",
                "title": "Institutional Mission and Institutional Capacity",
                "description": "The institution demonstrates strong commitment to a mission that emphasizes student learning and student achievement.",
                "category": "Mission and Capacity",
                "subcategory": "Institutional Mission",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Capacity Documentation", "Achievement Evidence"]
            },
            {
                "standard_id": "WASC_2",
                "accreditor_id": "wasc",
                "title": "Educational Effectiveness and Assessment",
                "description": "The institution demonstrates that student learning is the core theme of the institution's work and uses the results of its assessment of student learning to inform academic and learning-support planning.",
                "category": "Educational Effectiveness",
                "subcategory": "Student Learning Assessment",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Assessment Plan", "Learning Outcomes", "Assessment Results", "Improvement Plans"]
            },
            
            # ===== HLC STANDARDS (North Central) =====
            {
                "standard_id": "HLC_1",
                "accreditor_id": "hlc",
                "title": "Mission",
                "description": "The institution's mission is clear and articulated publicly; it guides the institution's operations.",
                "category": "Mission",
                "subcategory": "Institutional Mission",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Public Communications", "Operational Alignment"]
            },
            {
                "standard_id": "HLC_3",
                "accreditor_id": "hlc",
                "title": "Teaching and Learning: Quality, Resources, and Support",
                "description": "The institution provides high quality education, wherever and however its offerings are delivered.",
                "category": "Teaching and Learning",
                "subcategory": "Educational Quality",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Academic Programs", "Faculty Qualifications", "Learning Resources", "Student Support"]
            },
            {
                "standard_id": "HLC_4",
                "accreditor_id": "hlc",
                "title": "Teaching and Learning: Evaluation and Improvement",
                "description": "The institution demonstrates responsibility for the quality of its educational programs, learning environments, and support services.",
                "category": "Evaluation and Improvement",
                "subcategory": "Quality Assurance",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Program Assessment", "Improvement Plans", "Quality Measures", "Systematic Evaluation"]
            },
            
            # ===== NWCCU STANDARDS (Northwest) =====
            {
                "standard_id": "NWCCU_1",
                "accreditor_id": "nwccu",
                "title": "Mission, Core Themes, and Expectations",
                "description": "The institution defines mission, core themes, and expectations of achievement and uses these to guide planning and resource allocation.",
                "category": "Mission and Core Themes",
                "subcategory": "Institutional Mission",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Mission Statement", "Core Theme Identification", "Planning Documents"]
            },
            {
                "standard_id": "NWCCU_2",
                "accreditor_id": "nwccu",
                "title": "Resources and Capacity",
                "description": "The institution has adequate and appropriate human, financial, physical, and information resources to achieve its mission and core themes.",
                "category": "Resources and Capacity",
                "subcategory": "Institutional Resources",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Resource Documentation", "Financial Records", "Capacity Assessment", "Infrastructure Plans"]
            },
            
            # ===== SPECIAL REQUIREMENTS =====
            {
                "standard_id": "QEP_GENERAL",
                "accreditor_id": "regional",
                "title": "Quality Enhancement Plan Requirements",
                "description": "Institutions must develop, implement, and assess a Quality Enhancement Plan that focuses on improving student learning outcomes.",
                "category": "Quality Enhancement",
                "subcategory": "QEP Implementation",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["QEP Document", "Implementation Plan", "Assessment Design", "Resource Allocation", "Timeline", "Outcome Measures"]
            },
            {
                "standard_id": "TITLE_IV_COMPLIANCE",
                "accreditor_id": "federal",
                "title": "Federal Compliance Requirements",
                "description": "The institution demonstrates compliance with federal regulations including Title IV financial aid requirements, student right-to-know, and other federal mandates.",
                "category": "Federal Compliance",
                "subcategory": "Regulatory Compliance",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": True,
                "evidence_requirements": ["Title IV Documentation", "Financial Aid Records", "Student Right-to-Know Reports", "Compliance Audits"]
            },
            {
                "standard_id": "DISTANCE_ED_COMPLIANCE",
                "accreditor_id": "regional",
                "title": "Distance Education Standards",
                "description": "Institutions offering distance education must demonstrate that programs maintain the same academic rigor and student support as traditional programs.",
                "category": "Distance Education",
                "subcategory": "Online Program Quality",
                "version": "2024",
                "effective_date": "2024-01-01",
                "is_required": False,
                "evidence_requirements": ["Distance Ed Policies", "Technology Infrastructure", "Student Authentication", "Academic Integrity Measures", "Student Support Services"]
            }
        ]
        
        standards_created = 0
        for standard in standards_data:
            try:
                # Check if standard already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM accreditation_standards WHERE standard_id = $1",
                    standard["standard_id"]
                )
                
                if existing:
                    continue
                
                # Insert new standard
                await conn.execute("""
                    INSERT INTO accreditation_standards (
                        id, standard_id, accreditor_id, title, description, 
                        category, subcategory, version, effective_date, 
                        is_required, evidence_requirements, created_at
                    ) VALUES (
                        gen_random_uuid()::text, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                """, 
                    standard["standard_id"],
                    standard["accreditor_id"],
                    standard["title"],
                    standard["description"],
                    standard["category"],
                    standard["subcategory"],
                    standard["version"],
                    datetime.fromisoformat(standard["effective_date"]),
                    standard["is_required"],
                    standard["evidence_requirements"],
                    datetime.utcnow()
                )
                standards_created += 1
                
            except Exception as e:
                logger.error(f"Failed to create standard {standard['standard_id']}: {e}")
        
        # Get counts by accreditor
        accreditor_counts = {}
        accreditors = ['sacscoc', 'neche', 'msche', 'wasc', 'hlc', 'nwccu', 'regional', 'federal']
        
        for accreditor in accreditors:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM accreditation_standards WHERE accreditor_id = $1", 
                accreditor
            )
            if count > 0:
                accreditor_counts[accreditor] = count
        
        total_standards = await conn.fetchval("SELECT COUNT(*) FROM accreditation_standards")
        
        await conn.close()
        
        return {
            "success": True,
            "message": f"Comprehensive US accreditation standards seeding complete! Created {standards_created} new standards",
            "standards_created": standards_created,
            "total_standards": total_standards,
            "accreditor_breakdown": accreditor_counts,
            "accreditors_included": [
                "SACSCOC (Southern Association of Colleges and Schools)",
                "NECHE (New England Commission of Higher Education)", 
                "MSCHE (Middle States Commission on Higher Education)",
                "WASC (Western Association of Schools and Colleges)",
                "HLC (Higher Learning Commission - North Central)",
                "NWCCU (Northwest Commission on Colleges and Universities)",
                "QEP (Quality Enhancement Plan) Requirements",
                "Federal Compliance Requirements",
                "Distance Education Standards"
            ]
        }
        
    except Exception as e:
        logger.error(f"Standards seeding error: {e}")
        return {"success": False, "error": str(e), "error_type": type(e).__name__}

@router.post("/debug/seed-standards-simple", include_in_schema=False)
async def seed_standards_simple():
    """Simple standards seeding endpoint that uses the same approach as migrate-users"""
    try:
        import asyncpg
        import os
        from datetime import datetime
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {"error": "DATABASE_URL not found"}
            
        conn = await asyncpg.connect(database_url)
        
        # Check if standards already exist
        existing_count = await conn.fetchval("SELECT COUNT(*) FROM accreditation_standards")
        if existing_count > 0:
            await conn.close()
            return {
                "success": True,
                "message": f"Standards already exist ({existing_count} found). Skipping seeding.",
                "existing_standards": existing_count
            }
        
        # Simple set of core standards for immediate functionality
        core_standards = [
            ("SACSCOC_1_1", "sacscoc", "Mission", "The institution has a clearly defined mission statement.", "Mission", "Institutional Mission", True),
            ("SACSCOC_QEP", "sacscoc", "Quality Enhancement Plan", "Institution develops and implements a QEP.", "Quality Enhancement", "QEP Implementation", True),
            ("NECHE_1", "neche", "Mission and Purposes", "Institution's mission is appropriate to higher education.", "Mission", "Institutional Mission", True),
            ("MSCHE_I", "msche", "Mission and Goals", "Institution's mission defines its purpose.", "Mission", "Institutional Mission", True),
            ("WASC_1", "wasc", "Institutional Mission", "Institution demonstrates strong commitment to mission.", "Mission", "Institutional Mission", True),
            ("HLC_1", "hlc", "Mission", "Institution's mission is clear and articulated publicly.", "Mission", "Institutional Mission", True),
            ("NWCCU_1", "nwccu", "Mission and Core Themes", "Institution defines mission and core themes.", "Mission", "Institutional Mission", True),
            ("QEP_GENERAL", "regional", "QEP Requirements", "Institutions must develop and implement a QEP.", "Quality Enhancement", "QEP Implementation", True),
            ("FEDERAL_COMPLIANCE", "federal", "Federal Compliance", "Institution demonstrates federal compliance.", "Compliance", "Regulatory Compliance", True),
        ]
        
        standards_created = 0
        for standard_data in core_standards:
            try:
                await conn.execute("""
                    INSERT INTO accreditation_standards (
                        id, standard_id, accreditor_id, title, description, 
                        category, subcategory, version, effective_date, 
                        is_required, evidence_requirements, created_at
                    ) VALUES (
                        gen_random_uuid()::text, $1, $2, $3, $4, $5, $6, '2024', $7, $8, 
                        ARRAY['Documentation Required'], $9
                    )
                """, 
                    standard_data[0],  # standard_id
                    standard_data[1],  # accreditor_id
                    standard_data[2],  # title
                    standard_data[3],  # description
                    standard_data[4],  # category
                    standard_data[5],  # subcategory
                    datetime.fromisoformat("2024-01-01"),  # effective_date
                    standard_data[6],  # is_required
                    datetime.utcnow()   # created_at
                )
                standards_created += 1
                
            except Exception as e:
                logger.error(f"Failed to create standard {standard_data[0]}: {e}")
        
        total_standards = await conn.fetchval("SELECT COUNT(*) FROM accreditation_standards")
        await conn.close()
        
        return {
            "success": True,
            "message": f"Core accreditation standards seeded! Created {standards_created} standards",
            "standards_created": standards_created,
            "total_standards": total_standards
        }
        
    except Exception as e:
        logger.error(f"Simple standards seeding error: {e}")
        return {"success": False, "error": str(e), "error_type": type(e).__name__}
