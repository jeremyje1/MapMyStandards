#!/usr/bin/env python3
"""
Test the deployed MapMyStandards backend
"""

import requests


def test_deployment(base_url):
    """Test the deployed backend"""

    print(f"🧪 Testing MapMyStandards deployment at: {base_url}")
    print("=" * 60)

    # Test 1: Health Check
    try:
        print("1️⃣ Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check PASSED")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ Health check FAILED - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check ERROR: {e}")

    # Test 2: Root endpoint
    try:
        print("\n2️⃣ Testing root endpoint...")
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint PASSED")
        else:
            print(f"❌ Root endpoint - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint ERROR: {e}")

    # Test 3: Login page
    try:
        print("\n3️⃣ Testing login page...")
        response = requests.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ Login page PASSED")
        else:
            print(f"❌ Login page - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Login page ERROR: {e}")

    print("\n" + "=" * 60)
    print("🎉 Deployment test complete!")
    print(f"🔗 Your backend is live at: {base_url}")
    print(f"🔗 Health check: {base_url}/health")
    print(f"🔗 Login page: {base_url}/login")
    print(f"🔗 Webhook endpoint: {base_url}/webhook")


if __name__ == "__main__":
    # You'll need to replace this with your actual Railway URL
    railway_url = input("Enter your Railway URL (e.g., https://your-app.railway.app): ").strip()

    if railway_url:
        test_deployment(railway_url)
    else:
        print("❌ Please provide your Railway URL")
        print("💡 You can find it in your Railway dashboard or by running 'railway status'")
