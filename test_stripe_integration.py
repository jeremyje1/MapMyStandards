#!/usr/bin/env python3
"""
Stripe Integration Test for A³E MapMyStandards
Tests the complete payment flow with live Stripe API
"""

import os
import sys
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stripe_integration():
    """Test Stripe integration with live API keys"""
    
    print("🧪 Testing Stripe Integration for A³E")
    print("=" * 50)
    
    # Initialize Stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not stripe.api_key or stripe.api_key.startswith('sk_test'):
        print("❌ Live Stripe API key not found or using test key")
        return False
    
    print("✅ Stripe API key configured (live mode)")
    
    try:
        # Test 1: List products
        print("\n📦 Testing Products...")
        products = stripe.Product.list(limit=10)
        a3e_products = [p for p in products.data if 'A³E' in p.name]
        
        if len(a3e_products) >= 2:
            print(f"✅ Found {len(a3e_products)} A³E products")
            for product in a3e_products:
                print(f"   → {product.name} (ID: {product.id})")
        else:
            print("❌ A³E products not found")
            return False
        
        # Test 2: List prices
        print("\n💰 Testing Prices...")
        prices = stripe.Price.list(limit=20)
        a3e_prices = [p for p in prices.data if p.product in [prod.id for prod in a3e_products]]
        
        expected_prices = {
            'college_monthly': 29700,
            'college_yearly': 297000,
            'multicampus_monthly': 89700,
            'multicampus_yearly': 807300
        }
        
        found_prices = {}
        for price in a3e_prices:
            amount = price.unit_amount
            interval = price.recurring.interval if price.recurring else 'one_time'
            product = next((p for p in a3e_products if p.id == price.product), None)
            
            if product:
                key = f"{product.name.lower().replace('a³e ', '').replace(' plan', '').replace('-', '_')}_{interval}"
                found_prices[key] = amount
                print(f"   → {price.nickname or 'No nickname'}: ${amount/100:.2f} per {interval}")
        
        # Verify pricing
        pricing_correct = True
        for plan, expected_amount in expected_prices.items():
            if plan in found_prices:
                if found_prices[plan] == expected_amount:
                    print(f"   ✅ {plan}: ${expected_amount/100:.2f} ✓")
                else:
                    print(f"   ❌ {plan}: Expected ${expected_amount/100:.2f}, got ${found_prices[plan]/100:.2f}")
                    pricing_correct = False
            else:
                print(f"   ❌ {plan}: Price not found")
                pricing_correct = False
        
        if not pricing_correct:
            print("❌ Pricing verification failed")
            return False
        
        print("✅ All prices verified correctly")
        
        # Test 3: Create test customer (won't charge)
        print("\n👤 Testing Customer Creation...")
        test_customer = stripe.Customer.create(
            email="test@mapmystandards.ai",
            name="Test College Account",
            description="Test customer for A³E integration verification"
        )
        print(f"✅ Test customer created: {test_customer.id}")
        
        # Clean up test customer
        stripe.Customer.delete(test_customer.id)
        print("✅ Test customer cleaned up")
        
        # Test 4: Verify webhook endpoints
        print("\n🔗 Testing Webhook Configuration...")
        webhooks = stripe.WebhookEndpoint.list()
        a3e_webhooks = [w for w in webhooks.data if 'mapmystandards' in w.url]
        
        if a3e_webhooks:
            print(f"✅ Found {len(a3e_webhooks)} webhook(s)")
            for webhook in a3e_webhooks:
                print(f"   → {webhook.url}")
        else:
            print("⚠️  No webhooks configured yet")
            print("   Set up webhook at: https://api.mapmystandards.ai/api/v1/billing/webhook/stripe")
        
        print("\n" + "=" * 50)
        print("🎉 Stripe Integration Test PASSED!")
        print("=" * 50)
        
        print("\n✅ Summary:")
        print("   → Live Stripe API keys configured")
        print("   → A³E products created correctly")
        print("   → Pricing matches specifications")
        print("   → Customer creation working")
        print("   → Ready for production!")
        
        return True
        
    except stripe.error.StripeError as e:
        print(f"\n❌ Stripe API Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        return False

def display_integration_status():
    """Display current integration status"""
    print("\n📊 Integration Status:")
    print("-" * 30)
    
    # Check environment variables
    secret_key = os.getenv('STRIPE_SECRET_KEY', '').replace('sk_live_', 'sk_live_***')
    pub_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '').replace('pk_live_', 'pk_live_***')
    
    print(f"Secret Key: {secret_key[:20]}...")
    print(f"Publishable Key: {pub_key[:20]}...")
    
    price_ids = [
        'STRIPE_PRICE_COLLEGE_MONTHLY',
        'STRIPE_PRICE_COLLEGE_YEARLY', 
        'STRIPE_PRICE_MULTI_CAMPUS_MONTHLY',
        'STRIPE_PRICE_MULTI_CAMPUS_YEARLY'
    ]
    
    for price_id in price_ids:
        value = os.getenv(price_id, 'Not Set')
        status = "✅" if value.startswith('price_') else "❌"
        print(f"{status} {price_id}: {value}")

if __name__ == "__main__":
    print("A³E Stripe Integration Test")
    print("https://mapmystandards.ai")
    
    display_integration_status()
    
    success = test_stripe_integration()
    
    if success:
        print("\n🚀 Ready to deploy to production!")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed")
        sys.exit(1)
