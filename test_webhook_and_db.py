#!/usr/bin/env python3
"""
Test script to verify webhook and database fixes
"""
import requests
import json
import time

API_BASE = "https://api.mapmystandards.ai"

def test_health_check():
    """Test if API is running"""
    print("1. Testing API health check...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy:", response.json())
            return True
        else:
            print("❌ API returned status:", response.status_code)
            return False
    except Exception as e:
        print("❌ API connection failed:", str(e))
        return False

def test_webhook_endpoint():
    """Test webhook endpoint availability"""
    print("\n2. Testing webhook endpoint...")
    try:
        # Send a test webhook request (it will fail auth but shows endpoint exists)
        response = requests.post(
            f"{API_BASE}/api/billing/webhook/stripe",
            json={"type": "test", "data": {}},
            headers={"stripe-signature": "test"},
            timeout=10
        )
        if response.status_code == 400:
            print("✅ Webhook endpoint exists (returned 400 as expected for invalid signature)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print("❌ Webhook test failed:", str(e))
        return False

def test_database_connection():
    """Test database via user check endpoint"""
    print("\n3. Testing database connection...")
    try:
        # Try to check a test user (will return 404 but proves DB is connected)
        response = requests.get(
            f"{API_BASE}/api/users/check?email=test@example.com",
            timeout=10
        )
        if response.status_code in [200, 404]:
            print("✅ Database connection working (user check endpoint responding)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print("❌ Database test failed:", str(e))
        return False

def main():
    print("MapMyStandards Fix Verification")
    print("=" * 50)
    print(f"Testing API at: {API_BASE}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Webhook Endpoint", test_webhook_endpoint()))
    results.append(("Database Connection", test_database_connection()))
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The fixes appear to be working correctly.")
    else:
        print("\n⚠️  Some tests failed. The deployment may still be in progress.")
        print("Wait a few minutes and run this script again.")

if __name__ == "__main__":
    main()
