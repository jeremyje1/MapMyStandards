"""Simplified billing routes for single $199/month plan (hosted Checkout).

Adds diagnostics & legacy path alias (/api/billing/*) to avoid 404s when
older frontend code (or Stripe webhooks) still reference the non-versioned prefix.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import stripe
import os
import logging
from typing import Optional, Dict

from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
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
        os.getenv("STRIPE_PRICE_COLLEGE_MONTHLY"),  # legacy naming
        os.getenv("STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY"),
    ]
    for cid in candidates:
        if cid and cid.strip() and not cid.startswith("sk_"):
            return cid.strip()
    return ""  # force error if still empty

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
    """Simple checkout request - no plan selection needed"""
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

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
    if current_user and current_user.get('email'):
        checkout_params['customer_email'] = current_user['email']
        checkout_params['metadata'] = {
            'user_id': str(current_user.get('id', '')),
            'email': current_user['email']
        }
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
async def create_single_plan_checkout(request: CreateCheckoutRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """Primary (versioned) endpoint to create hosted checkout session."""
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
async def legacy_create_single_plan_checkout(request: CreateCheckoutRequest, current_user: Optional[dict] = Depends(get_current_user)):
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

@router.get("/verify-session", response_model=SessionVerifyResponse)
async def verify_session(session_id: str):
    """Verify a completed Checkout Session and return subscription + customer info.

    Frontend flow: After redirect with ?session_id=cs_test_123, call this endpoint.
    Use response to confirm success and optionally create/login user.
    """
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
        return SessionVerifyResponse(
            success=True,
            status="complete",
            customer_email=customer_email,
            customer_id=customer_id,
            subscription_id=subscription_id,
            price_id=price_id or SINGLE_PLAN_PRICE_ID,
            message="Checkout session verified"
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
