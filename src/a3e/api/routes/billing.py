"""
Payment API Routes for A³E
Handles trial signup, subscription management, and billing
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging

try:
    from ...services.payment_service import PaymentService  # type: ignore
    _payment_service_available = True
except Exception as e:  # catch ImportError or dependency errors
    _payment_service_available = False
    _payment_service_import_error = e
from ...core.auth import verify_api_key

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
    try:
        # Create trial subscription with Stripe
        result = await payment_service.create_trial_subscription(
            email=request.email,
            plan=request.plan,
            payment_method_id=getattr(request, 'payment_method_id', None),
            coupon_code=request.coupon_code
        )
        
        if result['success']:
            return {
                "success": True,
                "message": "7-day free trial started successfully",
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
            
    except Exception as e:
        logger.error(f"Trial signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trial subscription")

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
async def stripe_webhook(request: dict):
    """Handle Stripe webhooks for payment events"""
    try:
        # Verify webhook signature
        # Process webhook events (payment success, failures, etc.)
        
        event_type = request.get("type")
        
        if event_type == "payment_intent.succeeded":
            # Handle successful payment
            await _handle_payment_success(request["data"]["object"])
        elif event_type == "invoice.payment_failed":
            # Handle failed payment
            await _handle_payment_failure(request["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            await _handle_subscription_cancelled(request["data"]["object"])
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )

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
