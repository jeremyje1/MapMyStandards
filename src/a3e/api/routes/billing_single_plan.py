"""Simplified billing routes for single $199/month plan"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import stripe
import os
import logging
from typing import Optional

from ..dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing-single"])

# Initialize Stripe with test or live key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Single plan configuration
SINGLE_PLAN_PRICE_ID = os.getenv("STRIPE_SINGLE_PLAN_PRICE_ID", "price_SINGLE_199_MONTHLY")
SINGLE_PLAN_AMOUNT = 19900  # $199.00 in cents

class CreateCheckoutRequest(BaseModel):
    """Simple checkout request - no plan selection needed"""
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

@router.post("/create-single-plan-checkout")
async def create_single_plan_checkout(
    request: CreateCheckoutRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Create checkout session for the single $199/month plan"""
    try:
        # Build checkout parameters
        checkout_params = {
            'mode': 'subscription',
            'line_items': [{
                'price': SINGLE_PLAN_PRICE_ID,
                'quantity': 1
            }],
            'success_url': request.success_url or os.getenv("STRIPE_SUCCESS_URL", "https://platform.mapmystandards.ai/dashboard.html?session_id={CHECKOUT_SESSION_ID}"),
            'cancel_url': request.cancel_url or os.getenv("STRIPE_CANCEL_URL", "https://platform.mapmystandards.ai/pricing.html"),
            'allow_promotion_codes': True
        }
        
        # Add customer info if logged in
        if current_user and current_user.get('email'):
            checkout_params['customer_email'] = current_user['email']
            checkout_params['metadata'] = {
                'user_id': str(current_user.get('id', '')),
                'email': current_user['email']
            }
        
        # Create session
        session = stripe.checkout.Session.create(**checkout_params)
        
        logger.info(f"Created single-plan checkout session: {session.id}")
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "plan": "standard",
            "amount": SINGLE_PLAN_AMOUNT,
            "display_amount": "$199/month"
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.get("/single-plan-info")
async def get_single_plan_info():
    """Get information about the single plan"""
    return {
        "plan": {
            "name": "MapMyStandards Platform",
            "price": SINGLE_PLAN_AMOUNT,
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
            "stripe_price_id": SINGLE_PLAN_PRICE_ID
        }
    }
