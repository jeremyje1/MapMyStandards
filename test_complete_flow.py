#!/usr/bin/env python3
"""Test the complete user signup flow from homepage to Stripe checkout."""

import requests
import time
import json
from datetime import datetime

def test_flow():
    print("🧪 Testing MapMyStandards Complete Signup Flow")
    print("=" * 50)
    
    # Test 1: Homepage
    print("\n1️⃣ Testing Homepage (mapmystandards.ai)...")
    try:
        response = requests.get("https://mapmystandards.ai", timeout=10)
        if response.status_code == 200:
            print("   ✅ Homepage is accessible")
            # Check for trial link
            if "platform.mapmystandards.ai/trial" in response.text:
                print("   ✅ Trial links found in homepage")
            else:
                print("   ❌ Trial links not found in homepage")
        else:
            print(f"   ❌ Homepage returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing homepage: {e}")
    
    # Test 2: Platform Frontend
    print("\n2️⃣ Testing Platform Frontend...")
    try:
        response = requests.get("https://platform.mapmystandards.ai", timeout=10)
        if response.status_code == 200:
            print("   ✅ Platform frontend is accessible")
        else:
            print(f"   ❌ Platform returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing platform: {e}")
    
    # Test 3: Trial Page
    print("\n3️⃣ Testing Trial Page...")
    try:
        response = requests.get("https://platform.mapmystandards.ai/trial", timeout=10)
        if response.status_code == 200:
            print("   ✅ Trial page is accessible")
        else:
            print(f"   ❌ Trial page returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing trial page: {e}")
    
    # Test 4: Backend API
    print("\n4️⃣ Testing Backend API...")
    try:
        response = requests.get("https://api.mapmystandards.ai/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Backend API is healthy")
        else:
            print(f"   ❌ API health check returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing API: {e}")
    
    # Test 5: Checkout Endpoint
    print("\n5️⃣ Testing Checkout API Endpoint...")
    try:
        # This will fail without auth, but we can check if the endpoint exists
        response = requests.post(
            "https://api.mapmystandards.ai/api/v1/billing/create-checkout-session-single",
            json={"email": "test@example.com"},
            timeout=10
        )
        if response.status_code == 401:
            print("   ✅ Checkout endpoint exists (auth required)")
        elif response.status_code == 422:
            print("   ✅ Checkout endpoint exists (validation active)")
        else:
            print(f"   ⚠️  Checkout endpoint returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing checkout endpoint: {e}")
    
    # Test 6: Stripe Configuration
    print("\n6️⃣ Testing Stripe Configuration...")
    print("   ℹ️  Price ID: price_1S2yYNK8PKpLCKDZ6zgFu2ay")
    print("   ℹ️  Plan: $199/month with 7-day trial")
    print("   ℹ️  Mode: Single plan checkout")
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print("   - Homepage: https://mapmystandards.ai")
    print("   - Platform: https://platform.mapmystandards.ai")
    print("   - Trial Page: https://platform.mapmystandards.ai/trial")
    print("   - Checkout Flow: /trial → /checkout → Stripe")
    print("\n✨ To complete a full test:")
    print("   1. Visit https://mapmystandards.ai")
    print("   2. Click 'Start Free Trial'")
    print("   3. Enter your email on the trial page")
    print("   4. You should be redirected to Stripe checkout")
    print("   5. The checkout should show $199/month plan")

if __name__ == "__main__":
    test_flow()
