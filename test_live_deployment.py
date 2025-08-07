#!/usr/bin/env python3
"""
Test the live MapMyStandards deployment
"""

import requests
import json

# Your live Railway URL
BACKEND_URL = "https://exemplary-solace-production-7f19.up.railway.app"

def test_live_deployment():
    """Test all endpoints of the live deployment"""
    
    print("🧪 TESTING LIVE MAPMY STANDARDS DEPLOYMENT")
    print("=" * 60)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check PASSED")
            print(f"   Response: {response.text}")
            tests_passed += 1
        else:
            print(f"❌ Health check FAILED - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check ERROR: {e}")
    
    # Test 2: Root Redirect
    print("\n2️⃣ Testing Root Endpoint...")
    try:
        response = requests.get(BACKEND_URL, timeout=10, allow_redirects=False)
        if response.status_code in [200, 302, 301]:
            print("✅ Root endpoint PASSED")
            print(f"   Status: {response.status_code}")
            tests_passed += 1
        else:
            print(f"❌ Root endpoint - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint ERROR: {e}")
    
    # Test 3: Login Page
    print("\n3️⃣ Testing Login Page...")
    try:
        response = requests.get(f"{BACKEND_URL}/login", timeout=10)
        if response.status_code == 200 and "MapMyStandards" in response.text:
            print("✅ Login page PASSED")
            print("   Login form loaded successfully")
            tests_passed += 1
        else:
            print(f"❌ Login page - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Login page ERROR: {e}")
    
    # Test 4: Webhook Endpoint
    print("\n4️⃣ Testing Webhook Endpoint...")
    try:
        response = requests.post(f"{BACKEND_URL}/webhook", 
                               json={}, 
                               timeout=10)
        if response.status_code in [200, 400]:  # 400 is expected for invalid webhook
            print("✅ Webhook endpoint PASSED")
            print("   Webhook endpoint is accessible")
            tests_passed += 1
        else:
            print(f"❌ Webhook endpoint - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook endpoint ERROR: {e}")
    
    # Results Summary
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Your deployment is working perfectly!")
    elif tests_passed >= 2:
        print("⚠️  Most tests passed. Your deployment is mostly working.")
    else:
        print("❌ Multiple tests failed. Check your deployment.")
    
    print("\n🔗 YOUR LIVE URLS:")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Health Check: {BACKEND_URL}/health")
    print(f"   Login: {BACKEND_URL}/login")
    print(f"   Webhook: {BACKEND_URL}/webhook")
    
    print("\n📋 NEXT STEPS:")
    print("1. Configure Stripe webhook with your Railway URL")
    print("2. Test signup flow from your Vercel frontend")
    print("3. Verify environment variables are working")
    print("4. Start accepting customers! 🚀")

if __name__ == "__main__":
    test_live_deployment()
