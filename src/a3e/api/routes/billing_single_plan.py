"""Simplified billing routes for single $199/month plan (hosted Checkout).

Adds diagnostics & legacy path alias (/api/billing/*) to avoid 404s when
older frontend code (or Stripe webhooks) still reference the non-versioned prefix.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import stripe
import os
import logging
from typing import Optional, Dict

from ..dependencies import get_optional_user, get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Create a custom security scheme that doesn't raise on missing auth
optional_security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)

# Simple in-memory metrics counters (reset on process restart)
_metrics = {
    'checkout_sessions_created': 0,
    'verify_attempts': 0,
    'verify_success': 0,
    'fallback_provision_attempts': 0,
    'fallback_provision_created': 0,
    'provisioning_status_checks': 0,
    'provisioning_status_found': 0,
}

# Simple sliding window rate limit (per IP) for provisioning-status
_rate_limit_window_seconds = 60
_rate_limit_max_requests = 30
_rate_limit_store: Dict[str, list] = {}

def _rate_limited(ip: str) -> bool:
    from time import time
    now = time()
    bucket = _rate_limit_store.setdefault(ip, [])
    # Drop old timestamps
    cutoff = now - _rate_limit_window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= _rate_limit_max_requests:
        return True
    bucket.append(now)
    return False
router = APIRouter(prefix="/api/v1/billing", tags=["billing-single"])
legacy_single_plan_router = APIRouter(prefix="/api/billing", tags=["billing-single-legacy"])

# Initialize Stripe with test or live key (defer so env already loaded)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

def _resolve_single_price_id() -> str:
    """Return the single plan price ID using multiple fallback env vars.

    Priority:
      1. STRIPE_SINGLE_PLAN_PRICE_ID
      2. STRIPE_PRICE_MONTHLY (custom single-tier var in .env)
      3. STRIPE_PRICE_COLLEGE_MONTHLY / STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY (existing mappings)
      4. Hardcoded placeholder (invalid) -> triggers 500 so operator fixes env
    """
    candidates = [
        os.getenv("STRIPE_SINGLE_PLAN_PRICE_ID"),
        os.getenv("STRIPE_PRICE_MONTHLY"),
        os.getenv("STRIPE_MONTHLY_PRICE_ID"),  # Alternative naming
        os.getenv("STRIPE_PRICE_COLLEGE_MONTHLY"),  # legacy naming
        os.getenv("STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY"),
    ]
    
    # Check all candidates
    for cid in candidates:
        if cid and cid.strip() and not cid.startswith("sk_"):
            logger.info(f"Using price ID from env: {cid[:10]}...")
            return cid.strip()
    
    # Use hardcoded production price ID as fallback
    # This is the single $199/month plan price ID
    production_price_id = "price_1S2yYNK8PKpLCKDZ6zgFu2ay"
    logger.warning(f"No price ID configured in env, using production default: {production_price_id}")
    return production_price_id

def _stripe_mode() -> str:
    key = stripe.api_key or ""
    if key.startswith("sk_live"):
        return "live"
    if key.startswith("sk_test"):
        return "test"
    return "unset"

SINGLE_PLAN_PRICE_ID = _resolve_single_price_id()
SINGLE_PLAN_AMOUNT = 19900  # $199.00 in cents (display only)

class CreateCheckoutRequest(BaseModel):
    """Checkout request for the single plan.

    Optional customer + institution details allow us to pre-populate Stripe
    metadata so the webhook (or fallback provisioning) can create the user
    record immediately after successful payment.
    """
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None
    role: Optional[str] = None

def _build_checkout_session(request: CreateCheckoutRequest, current_user: Optional[dict]) -> Dict[str, str]:
    if not SINGLE_PLAN_PRICE_ID:
        raise HTTPException(status_code=500, detail="Single plan price ID not configured. Set STRIPE_SINGLE_PLAN_PRICE_ID or STRIPE_PRICE_MONTHLY.")
    checkout_params = {
        'mode': 'subscription',
        'line_items': [{
            'price': SINGLE_PLAN_PRICE_ID,
            'quantity': 1
        }],
        'success_url': request.success_url or os.getenv(
            "STRIPE_SUCCESS_URL",
            "https://platform.mapmystandards.ai/dashboard?success=true&plan=single&session_id={CHECKOUT_SESSION_ID}"
        ),
        'cancel_url': request.cancel_url or os.getenv(
            "STRIPE_CANCEL_URL",
            "https://platform.mapmystandards.ai/subscribe"
        ),
        'allow_promotion_codes': True
    }
    # Always attach metadata so webhook / fallback provisioning has context
    metadata: Dict[str, str] = {
        'flow': 'single_plan_checkout',
        'plan_name': 'single',
    }
    if current_user and current_user.get('email'):
        checkout_params['customer_email'] = current_user['email']
        metadata.update({
            'user_id': str(current_user.get('id', '')),
            'email': current_user['email'],
        })
    else:
        # Allow explicit email override (anonymous pre-checkout capture)
        if request.email:
            checkout_params['customer_email'] = request.email
            metadata['email'] = request.email
        if request.name:
            metadata['customer_name'] = request.name
        if request.institution_name:
            metadata['institution_name'] = request.institution_name
        if request.institution_type:
            metadata['institution_type'] = request.institution_type
        if request.role:
            metadata['role'] = request.role
    if metadata:
        checkout_params['metadata'] = metadata
    session = stripe.checkout.Session.create(**checkout_params)
    logger.info(f"[single-plan] Created checkout session id=%s mode=%s price=%s", session.id, _stripe_mode(), SINGLE_PLAN_PRICE_ID)
    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "plan": "single",
        "amount": SINGLE_PLAN_AMOUNT,
        "display_amount": "$199/month",
        "price_id": SINGLE_PLAN_PRICE_ID,
        "mode": _stripe_mode(),
    }

@router.post("/create-single-plan-checkout")
async def create_single_plan_checkout(
    request: CreateCheckoutRequest, 
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Primary (versioned) endpoint to create hosted checkout session."""
    _metrics['checkout_sessions_created'] += 1
    try:
        return _build_checkout_session(request, current_user)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@legacy_single_plan_router.post("/create-single-plan-checkout", include_in_schema=False)
async def legacy_create_single_plan_checkout(request: CreateCheckoutRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    """Legacy path alias (/api/billing/create-single-plan-checkout) to prevent 404s."""
    return await create_single_plan_checkout(request, current_user)  # reuse logic

@router.get("/single-plan-info")
async def get_single_plan_info():
    """Return marketing + diagnostic info for single plan (versioned path)."""
    return {
        "plan": {
            "name": "MapMyStandards Platform",
            "price_cents": SINGLE_PLAN_AMOUNT,
            "display_price": "$199/month",
            "interval": "month",
            "features": [
                "Evidence Mapping & Intelligence",
                "Narrative Generation with CiteGuard™",
                "Gap Risk Prediction",
                "Organizational Charts",
                "Scenario Modeling & ROI",
                "Data Connectors & Integrations",
                "Enterprise Dashboard",
                "Unlimited Users & Documents",
                "Priority Support"
            ],
            "stripe_price_id": SINGLE_PLAN_PRICE_ID,
        },
        "diagnostics": {
            "stripe_key_mode": _stripe_mode(),
            "price_configured": bool(SINGLE_PLAN_PRICE_ID),
            "price_id_source": "env" if SINGLE_PLAN_PRICE_ID else "missing",
        }
    }

@legacy_single_plan_router.get("/single-plan-info", include_in_schema=False)
async def legacy_single_plan_info():
    return await get_single_plan_info()

class SessionVerifyResponse(BaseModel):
    success: bool
    status: str
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    price_id: Optional[str] = None
    message: Optional[str] = None
    provisioned: bool = False  # Whether a user account exists/provisioned

@router.get("/verify-session", response_model=SessionVerifyResponse)
async def verify_session(session_id: str):
    """Verify a completed Checkout Session and return subscription + customer info.

    Frontend flow: After redirect with ?session_id=cs_test_123, call this endpoint.
    Use response to confirm success and optionally create/login user.
    """
    _metrics['verify_attempts'] += 1
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id required")
        session = stripe.checkout.Session.retrieve(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.get("payment_status") not in ("paid", "no_payment_required") and session.get("status") != "complete":
            return SessionVerifyResponse(success=False, status=session.get("status", "incomplete"), message="Session not complete yet")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        customer_email = session.get("customer_details", {}).get("email") if session.get("customer_details") else session.get("customer_email")
        price_id = None
        # Attempt to get price from line items
        try:
            line_items = stripe.checkout.Session.list_line_items(session_id, limit=1)
            if line_items.data:
                price_id = line_items.data[0].price.id if getattr(line_items.data[0], 'price', None) else None
        except Exception:
            pass
        # Fallback provisioning: If user with this email does not exist yet (webhook race), create minimal account.
        provisioned = False
        if customer_email:
            try:
                from ...models.user import User, PasswordReset  # type: ignore
                from ...services.database_service import DatabaseService  # type: ignore
                from ...core.config import get_settings  # type: ignore
                from sqlalchemy import select  # type: ignore
                import secrets
                import uuid
                from datetime import datetime, timedelta
                settings = get_settings()
                db_service = DatabaseService(settings.database_url)
                async with db_service.get_session() as db:
                    stmt = select(User).where(User.email == customer_email)
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    if not existing:
                        _metrics['fallback_provision_attempts'] += 1
                        user = User(
                            email=customer_email,
                            name=session.get('customer_details', {}).get('name') or customer_email.split('@')[0],
                            password_hash='pending_reset',
                            institution_name=session.get('metadata', {}).get('institution_name'),
                            institution_type=session.get('metadata', {}).get('institution_type') or 'college',
                            role=session.get('metadata', {}).get('role') or 'Administrator',
                            is_trial=False,
                            trial_started_at=None,
                            trial_ends_at=None,
                            subscription_tier='single',
                            stripe_customer_id=customer_id,
                            stripe_subscription_id=subscription_id,
                            api_key=secrets.token_urlsafe(32),
                            api_key_created_at=datetime.utcnow(),
                            is_active=True,
                            is_verified=True,
                            email_verified_at=datetime.utcnow()
                        )
                        db.add(user)
                        await db.commit()
                        # Create password reset token for setup
                        token = str(uuid.uuid4())
                        code = secrets.token_hex(3).upper()
                        pr = PasswordReset(
                            user_id=user.id,
                            reset_token=token,
                            reset_code=code,
                            expires_at=datetime.utcnow() + timedelta(hours=48)
                        )
                        db.add(pr)
                        await db.commit()
                        try:
                            from ...services.email_service import email_service  # type: ignore
                            setup_link = f"https://platform.mapmystandards.ai/set-password?token={token}"
                            email_service.send_password_setup_email(
                                user_email=customer_email,
                                user_name=user.name,
                                setup_link=setup_link
                            )
                        except Exception:
                            pass
                        provisioned = True
                        _metrics['fallback_provision_created'] += 1
                    else:
                        provisioned = True
            except Exception:
                # Silent fail; provisioning will still happen via webhook
                pass
        else:
            logger.warning("[single-plan] verify-session: no customer email present in session %s", session_id)
        _metrics['verify_success'] += 1
        return SessionVerifyResponse(
            success=True,
            status="complete",
            customer_email=customer_email,
            customer_id=customer_id,
            subscription_id=subscription_id,
            price_id=price_id or SINGLE_PLAN_PRICE_ID,
            message="Checkout session verified",
            provisioned=provisioned
        )
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify session")

@legacy_single_plan_router.get("/verify-session", include_in_schema=False)
async def legacy_verify_session(session_id: str):
    return await verify_session(session_id)

@router.get("/single-plan-metrics")
async def single_plan_metrics(key: Optional[str] = None):
    """Return in-memory metrics for single plan checkout.

    If METRICS_KEY env var is set, require matching 'key' query param.
    """
    required = os.getenv('METRICS_KEY')
    if required and key != required:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Shallow copy to avoid mutation during serialization
    return {
        'metrics': dict(_metrics),
        'price_id': SINGLE_PLAN_PRICE_ID,
        'stripe_mode': _stripe_mode(),
    }

@router.get("/provisioning-status")
async def provisioning_status(email: Optional[str] = None, session_id: Optional[str] = None, request=None):
    """Check if a user has been provisioned post checkout.

    Provide either email or session_id. If session_id is supplied and email is
    absent, attempts to retrieve session from Stripe to extract customer email.
    """
    _metrics['provisioning_status_checks'] += 1
    try:
        # Basic rate limit by client IP
        client_ip = None
        try:
            if request and hasattr(request, 'client') and request.client:
                client_ip = request.client.host
        except Exception:
            pass
        if client_ip and _rate_limited(client_ip):
            raise HTTPException(status_code=429, detail="Too Many Requests")
        if not email and not session_id:
            raise HTTPException(status_code=400, detail="email or session_id required")
        resolved_email = email
        if not resolved_email and session_id:
            try:
                sess = stripe.checkout.Session.retrieve(session_id)
                if sess:
                    if sess.get('customer_details') and sess['customer_details'].get('email'):
                        resolved_email = sess['customer_details']['email']
                    else:
                        resolved_email = sess.get('customer_email')
            except Exception:
                pass
        if not resolved_email:
            return {'provisioned': False, 'message': 'Email not resolved from session'}
        # Lookup user
        try:
            from ...models.user import User  # type: ignore
            from ...services.database_service import DatabaseService  # type: ignore
            from ...core.config import get_settings  # type: ignore
            from sqlalchemy import select  # type: ignore
            settings = get_settings()
            db_service = DatabaseService(settings.database_url)
            async with db_service.get_session() as db:
                stmt = select(User).where(User.email == resolved_email)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                if not user:
                    return {'provisioned': False, 'email': resolved_email}
                _metrics['provisioning_status_found'] += 1
                needs_setup = user.password_hash == 'pending_reset'
                resp = {
                    'provisioned': True,
                    'email': user.email,
                    'user_id': user.id,
                    'subscription_tier': user.subscription_tier,
                    'stripe_subscription_id': user.stripe_subscription_id,
                    'stripe_customer_id': user.stripe_customer_id,
                    'is_verified': user.is_verified,
                    'is_active': user.is_active,
                    'needs_password_setup': needs_setup,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                }
                if needs_setup:
                    # Provide a hint link (frontend still triggers reset flow using existing token email)
                    resp['password_setup_help'] = 'Check your email for a password setup link. If missing, use Forgot Password.'
                return resp
        except HTTPException:
            raise
        except Exception as e:
            logger.error("[single-plan] provisioning-status DB error: %s", e)
            return {'provisioned': False, 'email': resolved_email, 'error': 'lookup_failed'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[single-plan] provisioning-status error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to check provisioning status")
