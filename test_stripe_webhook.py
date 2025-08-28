#!/usr/bin/env python3
"""
Test Stripe webhook configuration
"""
import requests
import json

def test_webhook():
    """Test webhook endpoint"""
    webhook_url = "https://api.mapmystandards.ai/api/v1/billing/webhook/stripe"
    
    print("Testing Stripe webhook endpoint...")
    print(f"URL: {webhook_url}")
    
    # Test with a GET request (should return method not allowed)
    try:
        response = requests.get(webhook_url, timeout=10)
        print(f"GET Status: {response.status_code}")
        if response.status_code == 405:
            print("✅ Webhook endpoint exists (POST only)")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_payment_endpoints():
    """Test payment-related endpoints"""
    base_url = "https://api.mapmystandards.ai/api/v1/billing"
    
    endpoints = [
        "/config/stripe-key",
        "/trial/diagnose", 
        "/trial/ping"
    ]
    
    print("\nTesting payment endpoints...")
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

if __name__ == "__main__":
    test_webhook()
    test_payment_endpoints()
    
    print("\n" + "="*50)
    print("WEBHOOK SETUP INSTRUCTIONS")
    print("="*50)
    print("1. Go to: https://dashboard.stripe.com/webhooks")
    print("2. Add endpoint: https://api.mapmystandards.ai/api/v1/billing/webhook/stripe")
    print("3. Select events:")
    print("   - customer.subscription.trial_will_end")
    print("   - customer.subscription.updated")  
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("4. Copy webhook secret to Railway variables")
    print("5. Set: STRIPE_WEBHOOK_SECRET=whsec_...")
    print("\nThis ensures payments are captured when trials end!")