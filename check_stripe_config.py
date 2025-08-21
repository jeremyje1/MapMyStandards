#!/usr/bin/env python3
"""
Check Stripe configuration and environment variables
"""
import os
import json
import requests

def check_stripe_config():
    print("🔍 Checking Stripe Configuration...")
    print("="*50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    stripe_vars = {
        "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY", "NOT SET"),
        "STRIPE_PUBLISHABLE_KEY": os.getenv("STRIPE_PUBLISHABLE_KEY", "NOT SET"),
        "STRIPE_WEBHOOK_SECRET": os.getenv("STRIPE_WEBHOOK_SECRET", "NOT SET")
    }
    
    for key, value in stripe_vars.items():
        if value == "NOT SET":
            print(f"❌ {key}: NOT SET")
        elif value.startswith("sk_test_") or value.startswith("pk_test_"):
            print(f"⚠️  {key}: TEST MODE ({value[:20]}...)")
        elif value.startswith("sk_live_") or value.startswith("pk_live_"):
            print(f"✅ {key}: LIVE MODE ({value[:20]}...)")
        else:
            print(f"❓ {key}: UNKNOWN ({value[:20]}...)")
    
    # Test the new endpoint
    print("\n🌐 Testing API Endpoint:")
    try:
        # Test local endpoint
        response = requests.get("http://localhost:8000/api/v1/billing/config/stripe-key")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local API Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Local API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️  Local API not available: {str(e)}")
    
    # Test production endpoint
    try:
        response = requests.get("https://platform.mapmystandards.ai/api/v1/billing/config/stripe-key")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Production API Response: {json.dumps(data, indent=2)}")
        else:
            print(f"\n❌ Production API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"\n⚠️  Production API error: {str(e)}")
    
    print("\n📝 Recommendations:")
    if not os.getenv("STRIPE_PUBLISHABLE_KEY"):
        print("1. Set STRIPE_PUBLISHABLE_KEY in Railway environment variables")
        print("   - Go to Railway dashboard > Variables")
        print("   - Add STRIPE_PUBLISHABLE_KEY with your Stripe publishable key")
    
    if not os.getenv("STRIPE_SECRET_KEY"):
        print("2. Set STRIPE_SECRET_KEY in Railway environment variables")
        print("   - Add STRIPE_SECRET_KEY with your Stripe secret key")
    
    print("\n💡 To get your Stripe keys:")
    print("   1. Log in to https://dashboard.stripe.com")
    print("   2. Go to Developers > API keys")
    print("   3. Copy the publishable and secret keys")
    print("   4. Add them to Railway environment variables")

if __name__ == "__main__":
    check_stripe_config()
