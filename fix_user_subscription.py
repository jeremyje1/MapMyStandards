#!/usr/bin/env python3
"""
Fix missing Stripe subscription for existing user
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime, timedelta
import stripe

async def fix_user_subscription():
    """Create Stripe customer and subscription for existing user"""
    
    email = "estrellasandstars@outlook.com"
    plan = "professional_monthly"  # Default plan
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if not stripe_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return
        
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    # Initialize Stripe
    stripe.api_key = stripe_key
    print(f"✅ Stripe initialized with key ending in ...{stripe_key[-4:]}")
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    print("✅ Connected to database")
    
    try:
        # Check if user exists
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1", 
            email
        )
        
        if not user:
            print(f"❌ User {email} not found in database")
            return
            
        print(f"✅ Found user: {user['email']} (ID: {user['id']})")
        
        # Check if already has Stripe customer
        if user.get('customer_id') and user.get('subscription_id'):
            print(f"✅ User already has Stripe customer: {user['customer_id']}")
            print(f"✅ User already has subscription: {user['subscription_id']}")
            return
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=email,
            name=user.get('name', 'Customer'),
            metadata={
                'user_id': str(user['id']),
                'institution': user.get('institution_name', ''),
                'source': 'retroactive_fix'
            }
        )
        print(f"✅ Created Stripe customer: {customer.id}")
        
        # Get price ID for plan
        price_id_map = {
            'professional_monthly': os.getenv('STRIPE_PRICE_COLLEGE_MONTHLY'),
            'professional_yearly': os.getenv('STRIPE_PRICE_COLLEGE_YEARLY'),
            'institution_monthly': os.getenv('STRIPE_PRICE_MULTI_CAMPUS_MONTHLY'),
            'institution_yearly': os.getenv('STRIPE_PRICE_MULTI_CAMPUS_YEARLY')
        }
        
        price_id = price_id_map.get(plan)
        if not price_id:
            print(f"❌ No price ID found for plan: {plan}")
            return
            
        print(f"✅ Using price ID: {price_id}")
        
        # Create subscription with 7-day trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            trial_period_days=7,
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            metadata={
                'user_id': str(user['id']),
                'institution': user.get('institution_name', ''),
                'source': 'retroactive_fix'
            }
        )
        print(f"✅ Created subscription: {subscription.id}")
        print(f"✅ Trial end: {datetime.fromtimestamp(subscription.trial_end)}")
        
        # Update user in database
        await conn.execute("""
            UPDATE users 
            SET customer_id = $1, 
                subscription_id = $2,
                trial_end = $3,
                subscription_tier = $4,
                updated_at = $5
            WHERE email = $6
        """, 
            customer.id,
            subscription.id,
            datetime.fromtimestamp(subscription.trial_end),
            plan,
            datetime.utcnow(),
            email
        )
        print(f"✅ Updated user record in database")
        
        # Verify update
        updated_user = await conn.fetchrow(
            "SELECT customer_id, subscription_id, trial_end FROM users WHERE email = $1", 
            email
        )
        print(f"✅ Verification - Customer ID: {updated_user['customer_id']}")
        print(f"✅ Verification - Subscription ID: {updated_user['subscription_id']}")
        print(f"✅ Verification - Trial End: {updated_user['trial_end']}")
        
        print(f"\n🎉 Successfully fixed subscription for {email}")
        print(f"🎉 Customer can now access the dashboard with proper billing")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_user_subscription())
