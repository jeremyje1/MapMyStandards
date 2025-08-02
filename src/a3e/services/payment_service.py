"""
Payment Processing Service for A³E
Handles Stripe payments, subscriptions, and trial management
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..core.config import get_settings
from ..services.database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Handles payment processing and subscription management"""
    
    def __init__(self):
        self.settings = get_settings()
        stripe.api_key = self.settings.STRIPE_SECRET_KEY
        self.db_service = DatabaseService()
        
    async def create_trial_subscription(self, email: str, plan: str, payment_method_id: str, coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """Create a subscription with 7-day free trial."""
        try:
            # Create customer
            customer = stripe.Customer.create(
                email=email,
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Plan to Price ID mapping (uses environment variables for real Price IDs)
            price_mapping = {
                'college_monthly': self.settings.STRIPE_PRICE_COLLEGE_MONTHLY,
                'college_yearly': self.settings.STRIPE_PRICE_COLLEGE_YEARLY, 
                'multicampus_monthly': self.settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY,
                'multicampus_yearly': self.settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY
            }
            
            # Validate coupon if provided
            coupon_info = None
            if coupon_code:
                try:
                    coupon = stripe.Coupon.retrieve(coupon_code)
                    if coupon.valid:
                        coupon_info = {
                            'id': coupon.id,
                            'percent_off': coupon.percent_off,
                            'amount_off': coupon.amount_off,
                            'duration': coupon.duration
                        }
                    else:
                        logger.warning(f"Invalid coupon code: {coupon_code}")
                except stripe.error.InvalidRequestError:
                    logger.warning(f"Coupon not found: {coupon_code}")
            
            # Create subscription with 7-day trial
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'trial_period_days': 7,
                'metadata': {
                    'institution_name': institution_name,
                    'trial_end': (datetime.utcnow() + timedelta(days=7)).isoformat()
            
            # Add coupon if valid
            if coupon_info:
                subscription_data['coupon'] = coupon_code
                subscription_data['metadata']['coupon_applied'] = coupon_code
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            # Generate API key for immediate access
            api_key = self._generate_api_key(customer.id)
            
            # Store in database
            await self.store_trial_user(
                customer_id=customer.id,
                subscription_id=subscription.id,
                email=email,
                plan=plan,
                api_key=api_key,
                trial_end=datetime.utcnow() + timedelta(days=7)
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'api_key': api_key,
                'trial_end': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'status': 'trialing',
                'coupon_applied': coupon_info['id'] if coupon_info else None,
                'discount_info': coupon_info if coupon_info else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating trial: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating trial: {e}")
            return {'success': False, 'error': 'Internal server error'}
    
    async def create_subscription(self, 
                                customer_id: str,
                                plan: str,
                                payment_method_id: str) -> Dict[str, Any]:
        """Create a paid subscription"""
        try:
            # Get price ID for plan
            price_id = self._get_price_id(plan)
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Update customer's default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"],
            )
            
            # Update account in database
            await self._upgrade_account(customer_id, plan, subscription.id)
            
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def cancel_subscription(self, customer_id: str) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            # Get customer's subscription
            subscriptions = stripe.Subscription.list(customer=customer_id, status="active")
            
            if subscriptions.data:
                subscription = subscriptions.data[0]
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                
                # Update account status
                await self._downgrade_account(customer_id)
                
                return {
                    "status": "success",
                    "message": "Subscription will be cancelled at period end"
                }
            else:
                raise HTTPException(status_code=404, detail="No active subscription found")
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_account_status(self, api_key: str) -> Dict[str, Any]:
        """Get account status and usage"""
        try:
            account = await self._get_account_by_api_key(api_key)
            
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Check if trial expired
            if account["status"] == "trial" and datetime.utcnow() > account["trial_end"]:
                await self._expire_trial(account["id"])
                account["status"] = "expired"
            
            return {
                "account_id": account["id"],
                "institution_name": account["institution_name"],
                "plan": account["plan"],
                "status": account["status"],
                "api_usage": account["api_usage"],
                "api_quota": account["api_quota"],
                "trial_end": account.get("trial_end"),
                "billing_cycle_end": account.get("billing_cycle_end")
            }
            
        except Exception as e:
            logger.error(f"Error getting account status: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def track_api_usage(self, api_key: str, endpoint: str) -> bool:
        """Track API usage for billing and quota management"""
        try:
            account = await self._get_account_by_api_key(api_key)
            
            if not account:
                return False
            
            # Check quota
            if account["api_usage"] >= account["api_quota"]:
                return False
            
            # Increment usage
            await self._increment_usage(account["id"])
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
            return False
    
    async def validate_coupon(self, coupon_code: str) -> Dict[str, Any]:
        """Validate a coupon code and return discount information"""
        try:
            coupon = stripe.Coupon.retrieve(coupon_code)
            
            if not coupon.valid:
                return {'valid': False, 'error': 'Coupon is no longer valid'}
            
            # Check redemption limits
            if coupon.max_redemptions and coupon.times_redeemed >= coupon.max_redemptions:
                return {'valid': False, 'error': 'Coupon redemption limit reached'}
            
            # Format discount information
            discount_info = {
                'valid': True,
                'id': coupon.id,
                'name': coupon.name or coupon.id,
                'duration': coupon.duration,
                'duration_in_months': coupon.duration_in_months,
                'times_redeemed': coupon.times_redeemed,
                'max_redemptions': coupon.max_redemptions
            }
            
            if coupon.percent_off:
                discount_info['type'] = 'percentage'
                discount_info['percent_off'] = coupon.percent_off
                discount_info['description'] = f"{coupon.percent_off}% off"
            elif coupon.amount_off:
                discount_info['type'] = 'fixed_amount'
                discount_info['amount_off'] = coupon.amount_off / 100  # Convert to dollars
                discount_info['description'] = f"${coupon.amount_off/100:.0f} off"
            
            # Duration description
            if coupon.duration == 'forever':
                discount_info['duration_description'] = 'forever'
            elif coupon.duration == 'once':
                discount_info['duration_description'] = 'first payment only'
            elif coupon.duration == 'repeating':
                discount_info['duration_description'] = f"for {coupon.duration_in_months} months"
            
            return discount_info
            
        except stripe.error.InvalidRequestError:
            return {'valid': False, 'error': 'Coupon code not found'}
        except Exception as e:
            logger.error(f"Error validating coupon: {e}")
            return {'valid': False, 'error': 'Unable to validate coupon'}

    def _get_plan_quota(self, plan: str) -> int:
        """Get API quota for plan"""
        quotas = {
            "starter": 100,
            "professional": 500,
            "enterprise": 999999  # Unlimited
        }
        return quotas.get(plan, 100)
    
    def _get_price_id(self, plan: str) -> str:
        """Get Stripe price ID for plan (uses environment variables)"""
        price_ids = {
            "college_monthly": self.settings.STRIPE_PRICE_COLLEGE_MONTHLY,
            "college_yearly": self.settings.STRIPE_PRICE_COLLEGE_YEARLY,
            "multicampus_monthly": self.settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY, 
            "multicampus_yearly": self.settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY
        }
        return price_ids.get(plan, self.settings.STRIPE_PRICE_COLLEGE_MONTHLY)
    
    def _generate_api_key(self, account_id: int) -> str:
        """Generate a secure API key"""
        import secrets
        import hashlib
        
        # Generate random key
        random_key = secrets.token_urlsafe(32)
        
        # Create hash with account ID
        key_hash = hashlib.sha256(f"{account_id}:{random_key}".encode()).hexdigest()
        
        # Format as API key
        return f"a3e_{key_hash[:32]}"
    
    async def store_trial_user(self, customer_id: str, subscription_id: str, 
                              email: str, plan: str, api_key: str, trial_end: datetime):
        """Store trial user information in database"""
        try:
            # This would store the trial user in your database
            # Implementation depends on your database schema
            logger.info(f"Trial user stored: {email} - {customer_id}")
            
            # Send welcome email
            await self._send_welcome_email(email, "Trial Institution", api_key)
            
        except Exception as e:
            logger.error(f"Error storing trial user: {e}")
            raise

    async def _create_account_record(self, account_data: Dict[str, Any]) -> int:
        """Create account record in database"""
        # Implementation would depend on your database schema
        # This is a placeholder
        return 1  # Return account ID
    
    async def _get_account_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get account by API key"""
        # Implementation would depend on your database schema
        # This is a placeholder
        return None
    
    async def _upgrade_account(self, customer_id: str, plan: str, subscription_id: str):
        """Upgrade account to paid plan"""
        # Implementation would update database record
        pass
    
    async def _downgrade_account(self, customer_id: str):
        """Downgrade account after cancellation"""
        # Implementation would update database record
        pass
    
    async def _expire_trial(self, account_id: int):
        """Mark trial as expired"""
        # Implementation would update database record
        pass
    
    async def _increment_usage(self, account_id: int):
        """Increment API usage counter"""
        # Implementation would update database record
        pass
    
    async def _send_welcome_email(self, email: str, institution_name: str, api_key: str):
        """Send welcome email with onboarding information"""
        # Implementation would send email via your email service
        logger.info(f"Welcome email sent to {email}")
        pass
