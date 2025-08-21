"""
Payment Processing Service for A³E
Handles Stripe payments, subscriptions, and trial management
"""

import os
import stripe
import asyncio  # Added to allow background task for non-critical DB/email work
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..core.config import get_settings
from ..services.database_service import DatabaseService
try:
    from ..services.email_service import EmailService  # type: ignore
    _email_available = True
except Exception:
    _email_available = False
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Handles payment processing and subscription management"""
    
    def __init__(self):
        self.settings = get_settings()
        # Stripe API key may not be set in minimal deployments; guard access
        stripe_key = self.settings.STRIPE_SECRET_KEY
        if stripe_key:
            stripe.api_key = stripe_key
            logger.info(f"Stripe initialized with key ending in ...{stripe_key[-4:]}")
        else:
            logger.warning("No Stripe secret key found - payment features will not work")
            # Debug: check environment variables directly
            logger.warning(f"STRIPE_SECRET_KEY from env: {bool(os.getenv('STRIPE_SECRET_KEY'))}")
            logger.warning(f"STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY from env: {os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY', 'Not found')}")
        
        # Initialize database service lazily with configured database URL
        try:
            self.db_service = DatabaseService(self.settings.database_url)
        except Exception as e:
            logger.warning(f"Database service init skipped in PaymentService: {e}")
            self.db_service = None  # type: ignore
        
    async def create_trial_subscription(self, email: str, plan: str, payment_method_id: str, coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """Create a real Stripe trial subscription with 7-day free trial"""
        try:
            # Check if Stripe is configured
            if not stripe.api_key:
                logger.error("Stripe API key not configured - check STRIPE_SECRET_KEY environment variable")
                logger.error(f"Current settings has STRIPE_SECRET_KEY: {bool(self.settings.STRIPE_SECRET_KEY)}")
                logger.error(f"stripe.api_key is: {stripe.api_key}")
                return {'success': False, 'stage': 'precheck', 'error': 'Payment system not configured. Please contact support.'}
            
            # Helper to run blocking stripe calls in a thread
            async def _call(func, *f_args, **f_kwargs):
                # Use loop.run_in_executor for Python 3.8 compatibility
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, func, *f_args, **f_kwargs)

            logger.info("[trial] Starting customer lookup/create for %s", email)
            customers = await _call(stripe.Customer.list, email=email, limit=1)
            if customers.data:
                customer = customers.data[0]
                logger.info("[trial] Reusing existing customer %s", customer.id)
            else:
                customer = await _call(
                    stripe.Customer.create,
                    email=email,
                    payment_method=payment_method_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id,
                    }
                )
                logger.info("[trial] Created new customer %s", customer.id)
            
            # Attach payment method if not already attached
            try:
                await _call(
                    stripe.PaymentMethod.attach,
                    payment_method_id,
                    customer=customer.id,
                )
            except stripe.error.InvalidRequestError:
                # Payment method might already be attached
                pass
            
            # Get the price ID for the plan
            price_id = self._get_price_id(plan)
            logger.info(f"Price ID for plan '{plan}': {price_id}")
            
            if not price_id:
                logger.error(f"No price ID found for plan: {plan}")
                logger.error(
                    "Available price IDs (env) college=%s college_yearly=%s multicampus=%s multicampus_yearly=%s",
                    self.settings.STRIPE_PRICE_COLLEGE_MONTHLY,
                    getattr(self.settings, 'STRIPE_PRICE_COLLEGE_YEARLY', None),
                    self.settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY,
                    getattr(self.settings, 'STRIPE_PRICE_MULTI_CAMPUS_YEARLY', None)
                )
                return {'success': False, 'stage': 'price_lookup', 'error': f'Invalid plan selected: {plan}'}
            
            # Create subscription with trial
            subscription_params = {
                'customer': customer.id,
                'items': [{'price': price_id}],
                'trial_period_days': 7,
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent']
            }
            
            # Apply coupon if provided
            if coupon_code:
                subscription_params['coupon'] = coupon_code
            
            logger.info("[trial] Creating subscription for customer %s plan %s", customer.id, plan)
            subscription = await _call(stripe.Subscription.create, **subscription_params)
            logger.info("[trial] Subscription %s status=%s", subscription.id, getattr(subscription, 'status', None))
            
            # Generate API key
            api_key = self._generate_api_key(customer.id)
            
            # Store account info in database
            account_data = {
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'email': email,
                'api_key': api_key,
                'plan': plan,
                'status': 'trialing',
                'trial_end': datetime.fromtimestamp(subscription.trial_end).isoformat()
            }
            
            # Persist account + send password setup email in background so slow DB/email doesn't block checkout UX
            try:
                asyncio.create_task(self._create_account_record(account_data))  # fire and forget
            except Exception as bg_err:
                logger.warning(f"Failed to schedule account record creation task: {bg_err}")
            
            # Safely extract trial_end (can be None if no trial set)
            trial_end_ts = getattr(subscription, 'trial_end', None)
            if trial_end_ts:
                try:
                    trial_end_iso = datetime.fromtimestamp(trial_end_ts).isoformat()
                except Exception:
                    trial_end_iso = None
            else:
                trial_end_iso = None

            # Safely extract discount / coupon information (not present for most trial subscriptions)
            discount_info = None
            try:
                # subscription may be StripeObject (attr access) or dict-like
                raw_discount = getattr(subscription, 'discount', None)
                if not raw_discount and isinstance(subscription, dict):  # defensive
                    raw_discount = subscription.get('discount')
                if raw_discount:
                    # raw_discount may itself be a dict or StripeObject
                    coupon = getattr(raw_discount, 'coupon', None) or (raw_discount.get('coupon') if isinstance(raw_discount, dict) else None)
                    if coupon:
                        name = getattr(coupon, 'name', None) or (coupon.get('name') if isinstance(coupon, dict) else None)
                        percent_off = getattr(coupon, 'percent_off', None) or (coupon.get('percent_off') if isinstance(coupon, dict) else None)
                        amount_off = getattr(coupon, 'amount_off', None) or (coupon.get('amount_off') if isinstance(coupon, dict) else None)
                        discount_info = {
                            'name': name,
                            'percent_off': percent_off,
                            'amount_off': amount_off / 100 if amount_off else None
                        }
            except Exception as di_err:
                logger.debug(f"Unable to parse discount info (non-fatal): {di_err}")

            # Fire welcome email (non-blocking best-effort)
            try:
                if _email_available:
                    EmailService().send_welcome_email(email, email.split('@')[0])
                else:
                    logger.debug("Email service not available; skipping welcome email")
            except Exception as em_err:
                logger.warning(f"Unable to send welcome email: {em_err}")

            return {
                'success': True,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'api_key': api_key,
                'trial_end': trial_end_iso,
                'status': getattr(subscription, 'status', None) or (subscription.get('status') if isinstance(subscription, dict) else None),
                'coupon_applied': coupon_code if coupon_code else None,
                'discount_info': discount_info
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating trial subscription: {e}")
            return {'success': False, 'stage': 'stripe', 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating trial subscription: {e}")
            return {'success': False, 'stage': 'unexpected', 'error': 'Failed to create trial subscription'}
    
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
        # Temporary hardcoded price IDs from Railway environment
        # TODO: Fix environment variable loading issue
        hardcoded_price_ids = {
            "college": "price_1RyVQ4K8PKpLCKDZON0IMe3F",  # STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY
            "multicampus": "price_1RyVQgK8PKpLCKDZTais3Tyx",  # STRIPE_PRICE_ID_INSTITUTION_MONTHLY
            "college_monthly": "price_1RyVQ4K8PKpLCKDZON0IMe3F",
            "college_yearly": "price_1RyVQFK8PKpLCKDZ7KxYraxk",  # STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL
            "multicampus_monthly": "price_1RyVQgK8PKpLCKDZTais3Tyx",
            "multicampus_yearly": "price_1RyVQrK8PKpLCKDZUshqaOvZ"  # STRIPE_PRICE_ID_INSTITUTION_ANNUAL
        }
        
        # Try environment variables first, then fallback to hardcoded
        price_ids = {
            "college": self.settings.STRIPE_PRICE_COLLEGE_MONTHLY or os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY', '') or hardcoded_price_ids.get("college", ''),
            "multicampus": self.settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY or os.getenv('STRIPE_PRICE_ID_INSTITUTION_MONTHLY', '') or hardcoded_price_ids.get("multicampus", ''),
            "college_monthly": self.settings.STRIPE_PRICE_COLLEGE_MONTHLY or os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY', '') or hardcoded_price_ids.get("college_monthly", ''),
            "college_yearly": self.settings.STRIPE_PRICE_COLLEGE_YEARLY or os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL', '') or hardcoded_price_ids.get("college_yearly", ''),
            "multicampus_monthly": self.settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY or os.getenv('STRIPE_PRICE_ID_INSTITUTION_MONTHLY', '') or hardcoded_price_ids.get("multicampus_monthly", ''), 
            "multicampus_yearly": self.settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY or os.getenv('STRIPE_PRICE_ID_INSTITUTION_ANNUAL', '') or hardcoded_price_ids.get("multicampus_yearly", '')
        }
        price_id = price_ids.get(plan, '')
        
        # Debug logging
        if not price_id:
            logger.error(f"No price ID found for plan: {plan}")
            logger.error(f"Settings STRIPE_PRICE_COLLEGE_MONTHLY: {self.settings.STRIPE_PRICE_COLLEGE_MONTHLY}")
            logger.error(f"Direct env STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY: {os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY')}")
        else:
            logger.info(f"Using price ID {price_id} for plan {plan}")
        
        return price_id
    
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
        """Create or update user account + issue password setup token if new.

        Returns a pseudo account ID (1) for backward compatibility (TODO: real user.id).
        """
        try:
            from sqlalchemy import select
            from ..models.user import User, PasswordReset  # type: ignore
            if not self.db_service:
                logger.warning("DB service unavailable - cannot persist account")
                return 1
            async with self.db_service.get_session() as session:  # type: ignore
                # Find or create user
                result = await session.execute(select(User).where(User.email == account_data['email']))
                user = result.scalar_one_or_none()
                new_user = False
                if not user:
                    # Minimal user with placeholder password (must set via setup link)
                    import bcrypt
                    import secrets
                    placeholder = bcrypt.hashpw(secrets.token_hex(16).encode(), bcrypt.gensalt()).decode()
                    user = User(
                        email=account_data['email'],
                        name=account_data['email'].split('@')[0].title(),
                        password_hash=placeholder,
                        api_key=account_data['api_key'],
                        subscription_tier=account_data.get('plan', 'trial'),
                        stripe_customer_id=account_data.get('customer_id'),
                        stripe_subscription_id=account_data.get('subscription_id'),
                        is_trial=True,
                        trial_started_at=datetime.utcnow(),
                        trial_ends_at=datetime.fromisoformat(account_data['trial_end']) if account_data.get('trial_end') else None
                    )
                    session.add(user)
                    new_user = True
                else:
                    # Update Stripe / plan fields if missing
                    updated = False
                    for attr, key in [
                        ('stripe_customer_id', 'customer_id'),
                        ('stripe_subscription_id', 'subscription_id'),
                        ('subscription_tier', 'plan'),
                        ('api_key', 'api_key')
                    ]:
                        val = account_data.get(key)
                        if val and getattr(user, attr) != val:
                            setattr(user, attr, val)
                            updated = True
                    if updated:
                        user.updated_at = datetime.utcnow()
                await session.flush()

                if new_user:
                    # Create password setup token (PasswordReset entry reused)
                    import secrets
                    token = secrets.token_urlsafe(48)
                    code = secrets.token_hex(3)
                    expires_at = datetime.utcnow() + timedelta(hours=48)
                    reset = PasswordReset(
                        user_id=user.id,
                        reset_token=token,
                        reset_code=code,
                        expires_at=expires_at
                    )
                    session.add(reset)
                    await session.commit()

                    # Send password setup email (best-effort)
                    try:
                        if _email_available:
                            from ..services.email_service import EmailService  # type: ignore
                            base_url = getattr(self.settings, 'PUBLIC_APP_URL', None) or os.getenv('PUBLIC_APP_URL') or 'https://platform.mapmystandards.ai'
                            setup_link = f"{base_url}/set-password.html?token={token}"
                            EmailService().send_password_setup_email(user.email, user.name or user.email.split('@')[0], setup_link)
                        else:
                            logger.debug("Email service not available for password setup email")
                    except Exception as e:
                        logger.warning(f"Failed to send password setup email: {e}")
                else:
                    await session.commit()
            return 1
        except Exception as e:
            logger.warning(f"_create_account_record failed: {e}")
            return 1
    
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
    
    async def _send_welcome_email(self, email: str, institution_name: str, api_key: str):  # legacy helper (unused now)
        try:
            if _email_available:
                EmailService().send_welcome_email(email, institution_name or email.split('@')[0])
                logger.info(f"Welcome email dispatched to {email}")
            else:
                logger.debug("Email service not available for welcome email helper")
        except Exception as e:
            logger.warning(f"Welcome email helper failed: {e}")
