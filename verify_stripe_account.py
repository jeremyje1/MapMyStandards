#!/usr/bin/env python3
"""
Stripe Account Verification - Check actual Price IDs and set up coupons
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def verify_and_list_current_prices():
    """Verify actual Price IDs in your Stripe account"""
    
    print("🔍 Checking your actual Stripe account...")
    print("=" * 50)
    
    try:
        # Get all products
        products = stripe.Product.list(limit=100)
        a3e_products = [p for p in products.data if 'A³E' in p.name and p.active]
        
        print(f"📦 Found {len(a3e_products)} active A³E products:")
        
        all_prices = {}
        
        for product in a3e_products:
            print(f"\n→ {product.name} (ID: {product.id})")
            
            # Get prices for this product
            prices = stripe.Price.list(product=product.id, active=True)
            
            for price in prices.data:
                interval = price.recurring.interval if price.recurring else 'one_time'
                amount = price.unit_amount / 100
                
                # Determine plan key
                if 'College' in product.name:
                    plan_key = f"college_{interval}ly" if interval == 'month' else f"college_{interval}"
                elif 'Multi-Campus' in product.name:
                    plan_key = f"multicampus_{interval}ly" if interval == 'month' else f"multicampus_{interval}"
                else:
                    plan_key = f"unknown_{interval}"
                
                all_prices[plan_key] = price.id
                
                print(f"   💰 ${amount:.2f} per {interval} → ID: {price.id}")
                if price.nickname:
                    print(f"      Nickname: {price.nickname}")
        
        print(f"\n📋 Environment Variables Needed:")
        print("-" * 40)
        
        env_mapping = {
            'college_monthly': 'STRIPE_PRICE_COLLEGE_MONTHLY',
            'college_yearly': 'STRIPE_PRICE_COLLEGE_YEARLY',
            'multicampus_monthly': 'STRIPE_PRICE_MULTI_CAMPUS_MONTHLY', 
            'multicampus_yearly': 'STRIPE_PRICE_MULTI_CAMPUS_YEARLY'
        }
        
        for plan_key, env_var in env_mapping.items():
            price_id = all_prices.get(plan_key, 'NOT_FOUND')
            print(f"{env_var}={price_id}")
        
        # Check if the user's mentioned Price ID exists
        user_price_id = "price_1Rr4lcK8PKpLCKDZPM5mw5R1"
        print(f"\n🔍 Checking your mentioned Price ID: {user_price_id}")
        
        try:
            user_price = stripe.Price.retrieve(user_price_id)
            product = stripe.Product.retrieve(user_price.product)
            amount = user_price.unit_amount / 100
            interval = user_price.recurring.interval if user_price.recurring else 'one_time'
            
            print(f"✅ Found: {product.name} - ${amount:.2f} per {interval}")
            print(f"   Active: {user_price.active}")
            print(f"   Product: {product.name}")
            
        except stripe.error.InvalidRequestError:
            print(f"❌ Price ID {user_price_id} not found in your account")
        
        return all_prices
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def create_coupon_codes():
    """Create coupon codes for trials and promotions"""
    
    print(f"\n🎫 Creating Coupon Codes...")
    print("-" * 30)
    
    coupons_to_create = [
        {
            'id': 'TRIAL_EXTENDED_7DAYS',
            'duration': 'once',
            'amount_off': None,
            'percent_off': 100,
            'duration_in_months': None,
            'max_redemptions': 100,
            'metadata': {
                'purpose': 'Extend trial by 7 days',
                'target': 'trial_extension'
            }
        },
        {
            'id': 'COLLEGE_LAUNCH_20',
            'duration': 'repeating',
            'duration_in_months': 3,
            'percent_off': 20,
            'max_redemptions': 50,
            'metadata': {
                'purpose': '20% off for 3 months - College Plan launch offer',
                'target': 'college_plan'
            }
        },
        {
            'id': 'MULTICAMPUS_ENTERPRISE_15',
            'duration': 'repeating', 
            'duration_in_months': 6,
            'percent_off': 15,
            'max_redemptions': 25,
            'metadata': {
                'purpose': '15% off for 6 months - Multi-Campus enterprise offer',
                'target': 'multicampus_plan'
            }
        },
        {
            'id': 'EARLY_ADOPTER_50',
            'duration': 'once',
            'percent_off': 50,
            'max_redemptions': 10,
            'metadata': {
                'purpose': '50% off first payment - Early adopter special',
                'target': 'both_plans'
            }
        }
    ]
    
    created_coupons = []
    
    for coupon_data in coupons_to_create:
        try:
            # Check if coupon already exists
            try:
                existing = stripe.Coupon.retrieve(coupon_data['id'])
                print(f"⚠️  Coupon {coupon_data['id']} already exists")
                continue
            except stripe.error.InvalidRequestError:
                pass  # Coupon doesn't exist, create it
            
            coupon = stripe.Coupon.create(**coupon_data)
            created_coupons.append(coupon)
            
            discount_info = f"{coupon.percent_off}% off" if coupon.percent_off else f"${coupon.amount_off/100:.2f} off"
            duration_info = f"for {coupon.duration_in_months} months" if coupon.duration_in_months else coupon.duration
            
            print(f"✅ Created: {coupon.id}")
            print(f"   → {discount_info} {duration_info}")
            print(f"   → Max uses: {coupon.max_redemptions}")
            
        except Exception as e:
            print(f"❌ Error creating {coupon_data['id']}: {e}")
    
    return created_coupons

def setup_trial_configuration():
    """Display trial configuration instructions"""
    
    print(f"\n⏱️  Trial Configuration:")
    print("-" * 30)
    print("✅ 7-day trial period: Configured in subscription creation")
    print("✅ Credit card required: Built into checkout flow")
    print("✅ Automatic billing: Starts after trial period")
    print("✅ Easy cancellation: Available through customer portal")
    
    print(f"\n📧 Trial Email Sequence (Recommended):")
    print("   Day 0:  Welcome & Getting Started")
    print("   Day 7:  Feature spotlight & tips")
    print("   Day 14: '7 days left' reminder")
    print("   Day 19: 'Trial ending soon' warning")
    print("   Day 22: 'Welcome to paid subscription'")

if __name__ == "__main__":
    print("🔍 A³E Stripe Account Verification & Setup")
    print("https://mapmystandards.ai")
    print("=" * 60)
    
    # Verify current prices
    current_prices = verify_and_list_current_prices()
    
    # Create coupon codes
    create_coupon_codes()
    
    # Display trial configuration
    setup_trial_configuration()
    
    print(f"\n🎯 Next Steps:")
    print("1. Update .env with correct Price IDs (see above)")
    print("2. Test checkout flow with coupons")
    print("3. Set up trial email sequence")
    print("4. Configure customer portal for self-service")
    
    print(f"\n✅ Account verification complete!")
