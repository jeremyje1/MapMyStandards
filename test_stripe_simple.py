#!/usr/bin/env python3
"""Simple Stripe integration test using actual environment variables."""

import os
import sys
from dotenv import load_dotenv
import stripe

# Load environment variables
load_dotenv('.env.local')

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')

def main():
    print("🧪 Testing Stripe Integration")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('STRIPE_API_KEY')
    if not api_key:
        print("❌ STRIPE_API_KEY not found!")
        return
    
    print(f"✅ Using API key: {api_key[:20]}...")
    
    # Test connection
    try:
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.get('id')}")
        print(f"   Display name: {account.get('display_name', 'Not set')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test price IDs from environment
    print("\n💰 Testing Price IDs from environment:")
    
    monthly_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
    annual_id = os.getenv('STRIPE_ANNUAL_PRICE_ID')
    
    print(f"Monthly price ID: {monthly_id}")
    print(f"Annual price ID: {annual_id}")
    
    # Check monthly price
    if monthly_id:
        try:
            price = stripe.Price.retrieve(monthly_id)
            product = stripe.Product.retrieve(price.product)
            print(f"✅ Monthly subscription: {product.name}")
            print(f"   Amount: ${price.unit_amount / 100:.2f} {price.currency.upper()}/{price.recurring.interval}")
        except Exception as e:
            print(f"❌ Monthly price error: {e}")
    
    # Check annual price  
    if annual_id:
        try:
            price = stripe.Price.retrieve(annual_id)
            product = stripe.Product.retrieve(price.product)
            print(f"✅ Annual subscription: {product.name}")
            print(f"   Amount: ${price.unit_amount / 100:.2f} {price.currency.upper()}/{price.recurring.interval}")
        except Exception as e:
            print(f"❌ Annual price error: {e}")
    
    # Test creating a checkout session
    print("\n🛒 Testing checkout session creation:")
    try:
        session = stripe.checkout.Session.create(
            mode='subscription',
            payment_method_types=['card'],
            line_items=[{
                'price': monthly_id,
                'quantity': 1,
            }],
            success_url='http://localhost:3000/dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/pricing',
            metadata={
                'user_id': 'test_user_123',
                'plan_type': 'monthly'
            }
        )
        print(f"✅ Checkout session created successfully!")
        print(f"   Session ID: {session.id}")
        print(f"   URL: {session.url}")
    except Exception as e:
        print(f"❌ Checkout session error: {e}")
    
    # Check webhook secret
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if webhook_secret:
        print(f"\n🔒 Webhook secret configured: {webhook_secret[:20]}...")
    else:
        print("\n❌ STRIPE_WEBHOOK_SECRET not found!")
    
    print("\n✅ Stripe integration test complete!")
    print("\nNext steps:")
    print("1. Start the API server: python -m uvicorn src.a3e.main:app --reload")
    print("2. Start Stripe webhook listener: stripe listen --forward-to localhost:8000/webhooks/stripe")
    print("3. Test the API at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
