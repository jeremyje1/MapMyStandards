#!/usr/bin/env python3
"""
End-to-End Customer Flow Test for MapMyStandards Platform
Tests the complete customer journey from signup to subscription
"""

import requests
import json
import time
from datetime import datetime
from test_urls import API_BASE as BASE_URL
API_BASE = f"{BASE_URL.rstrip('/')}/api"

# Test user data
test_email = f"test_user_{int(time.time())}@example.com"
test_password = "TestPassword123!"
test_org = "Test University"

print("🧪 MapMyStandards E2E Customer Flow Test")
print("=" * 50)
print(f"Testing deployment at: {BASE_URL}")
print(f"Test email: {test_email}")
print("")

def test_api_health():
    """Test if the API is responding"""
    print("1️⃣ Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL.rstrip('/')}/", timeout=10)
    except Exception as e:
        print(f"   ❌ API not responding: {e}")
        return False
    print(f"   ✅ API is responding (Status: {response.status_code})")
    return True

def test_trial_signup():
    """Test trial account signup"""
    print("\n2️⃣ Testing Trial Signup...")
    
    signup_data = {
        "email": test_email,
        "password": test_password,
        "organization_name": test_org
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/trial/signup",
            json=signup_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Trial signup successful!")
            print(f"   - User ID: {data.get('user_id', 'N/A')}")
            print(f"   - Trial ends: {data.get('trial_ends_at', 'N/A')}")
            print(f"   - API Key: {data.get('api_key', 'N/A')[:20]}...")
            return data
        else:
            print(f"   ❌ Signup failed (Status: {response.status_code})")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_login(email, password):
    """Test user login"""
    print("\n3️⃣ Testing Login...")
    
    login_data = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful!")
            print(f"   - Access token received: {data.get('access_token', 'N/A')[:20]}...")
            return data.get('access_token')
        else:
            print(f"   ❌ Login failed (Status: {response.status_code})")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_trial_status(email, token=None):
    """Check trial status"""
    print("\n4️⃣ Testing Trial Status Check...")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(
            f"{API_BASE}/trial/status/{email}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Trial status retrieved!")
            print(f"   - Active: {data.get('is_trial_active', False)}")
            print(f"   - Days remaining: {data.get('days_remaining', 0)}")
            print(f"   - Expires: {data.get('trial_ends_at', 'N/A')}")
            return data
        else:
            print(f"   ❌ Status check failed (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_dashboard_access(token):
    """Test dashboard endpoints"""
    print("\n5️⃣ Testing Dashboard Access...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test overview endpoint
    try:
        response = requests.get(
            f"{API_BASE}/dashboard/overview",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Dashboard overview accessible!")
            print(f"   - Compliance score: {data.get('compliance_score', 0)}%")
            print(f"   - Documents: {data.get('total_documents', 0)}")
            return True
        else:
            print(f"   ❌ Dashboard access failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_checkout_session(email, token):
    """Test creating a Stripe checkout session"""
    print("\n6️⃣ Testing Stripe Checkout Session...")
    
    # This would normally be called from your frontend
    # For now, we'll just verify the endpoint exists
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # You might need to adjust this endpoint based on your actual implementation
        response = requests.post(
            f"{API_BASE}/payments/create-checkout",
            json={
                "email": email,
                "price_id": "price_1Rxb2wRMpSG47vNmCzxZGv5I",  # Monthly plan
                "success_url": f"{BASE_URL}/success",
                "cancel_url": f"{BASE_URL}/cancel"
            },
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   ✅ Checkout session created!")
            print(f"   - Session URL: {data.get('url', 'N/A')[:50]}...")
            return True
        elif response.status_code == 404:
            print(f"   ⚠️  Payment endpoint not found (might not be implemented yet)")
            return None
        else:
            print(f"   ❌ Checkout creation failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_static_pages():
    """Test static pages are accessible"""
    print("\n7️⃣ Testing Static Pages...")
    
    pages = [
        ("/", "Homepage"),
        ("/login", "Login page"),
        ("/signup", "Signup page"),
        ("/dashboard", "Dashboard"),
        ("/pricing", "Pricing page")
    ]
    
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", allow_redirects=True)
            if response.status_code == 200:
                print(f"   ✅ {name} accessible")
            else:
                print(f"   ⚠️  {name} returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name} error: {e}")

def main():
    """Run all tests"""
    
    # Test 1: API Health
    if not test_api_health():
        print("\n❌ API is not responding. Deployment might be starting up.")
        print("   Try again in a few moments.")
        return
    
    # Test 2: Trial Signup
    signup_result = test_trial_signup()
    if not signup_result:
        print("\n⚠️  Continuing with limited tests...")
    
    # Test 3: Login
    token = test_login(test_email, test_password)
    
    # Test 4: Trial Status
    test_trial_status(test_email, token)
    
    # Test 5: Dashboard Access
    if token:
        test_dashboard_access(token)
    
    # Test 6: Checkout Session
    if token:
        test_checkout_session(test_email, token)
    
    # Test 7: Static Pages
    test_static_pages()
    
    print("\n" + "=" * 50)
    print("✅ E2E Test Complete!")
    print("\n📊 Test Summary:")
    print(f"   - API URL: {BASE_URL}")
    print(f"   - Test user: {test_email}")
    print("\n🎯 Next Steps:")
    print("1. Check Railway logs: railway logs")
    print("2. Monitor Stripe dashboard for test payments")
    print("3. Verify email delivery in Postmark")

if __name__ == "__main__":
    main()
