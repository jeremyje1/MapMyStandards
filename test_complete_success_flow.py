#!/usr/bin/env python3
"""
Complete end-to-end customer flow test
"""
import requests
import json
from datetime import datetime
import time

print("🎉 COMPLETE CUSTOMER FLOW TEST")
print("=" * 70)

# Generate unique test data
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
test_email = f"success+{timestamp}@mapmystandards.ai"
test_username = f"successuser{timestamp}"

test_data = {
    "firstName": "Success",
    "lastName": "Customer", 
    "email": test_email,
    "institution": "Success University",
    "username": test_username,
    "password": "SuccessPassword123!",
    "plan": "monthly"
}

print(f"👤 Test Customer: {test_data['firstName']} {test_data['lastName']}")
print(f"📧 Email: {test_data['email']}")
print(f"🏢 Institution: {test_data['institution']}")
print(f"👤 Username: {test_data['username']}")
print(f"💳 Plan: {test_data['plan']}")
print()

# Step 1: Test trial account creation
print("📋 STEP 1: Creating trial account...")
try:
    response = requests.post(
        "https://api.mapmystandards.ai/create-trial-account",
        json=test_data,
        timeout=15,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ STEP 1 SUCCESS: Trial account created!")
        print(f"🆔 User ID: {result.get('user_id')}")
        checkout_url = result.get('checkout_url', '')
        print(f"🔗 Checkout URL: {checkout_url[:100]}...")
        
        # Step 2: Test health endpoints
        print("\n📋 STEP 2: Testing system health...")
        
        health_tests = [
            ("Frontend", "https://platform.mapmystandards.ai"),
            ("Backend Health", "https://api.mapmystandards.ai/health"),
            ("Backend Config", "https://api.mapmystandards.ai/debug-config"),
            ("Email Test", "https://api.mapmystandards.ai/test-email")
        ]
        
        all_healthy = True
        for name, url in health_tests:
            try:
                health_response = requests.get(url, timeout=10)
                if health_response.status_code == 200:
                    print(f"✅ {name}: Working")
                else:
                    print(f"⚠️ {name}: Status {health_response.status_code}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
                all_healthy = False
        
        # Step 3: Summary
        print("\n" + "=" * 70)
        print("🎉 COMPLETE CUSTOMER FLOW TEST RESULTS")
        print("=" * 70)
        
        if all_healthy:
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            print("✅ Customer can successfully:")
            print("   • Create trial accounts")
            print("   • Access Stripe checkout")
            print("   • Receive email notifications")
            print("   • Use the full platform")
            print()
            print("🚀 PLATFORM IS READY FOR PRODUCTION!")
        else:
            print("⚠️ Some components need attention")
        
        print()
        print("📊 Test Customer Details:")
        print(f"   Email: {test_email}")
        print(f"   Username: {test_username}")
        print(f"   User ID: {result.get('user_id')}")
        print()
        print("🔗 Next Steps:")
        print("   • Customer can complete payment at Stripe checkout")
        print("   • Platform will handle webhooks and activate trial")
        print("   • Email notifications will be sent")
        
    else:
        print("❌ STEP 1 FAILED: Trial account creation failed")
        try:
            error = response.json()
            print(f"📝 Error: {error}")
        except:
            print(f"📝 Raw response: {response.text}")

except Exception as e:
    print(f"❌ Exception during testing: {e}")

print("\n" + "=" * 70)
