#!/usr/bin/env python3
"""
Complete Platform Test for MapMyStandards
Tests both API endpoints and frontend pages
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "https://api.mapmystandards.ai"
FRONTEND_URL = "https://platform.mapmystandards.ai"

# Test user data
test_email = f"test_user_{int(time.time())}@example.com"
test_password = "TestPassword123!"
test_org = "Test University"

print("🧪 MapMyStandards Complete Platform Test")
print("=" * 50)
print(f"API URL: {API_URL}")
print(f"Frontend URL: {FRONTEND_URL}")
print(f"Test email: {test_email}")

def test_api_health():
    """Test API health endpoint"""
    print("\n1️⃣ Testing API Health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API is healthy (Status: {data['status']})")
            print(f"   Version: {data['version']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Services: {json.dumps(data['services'], indent=6)}")
            return True
        else:
            print(f"   ❌ API health check failed (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ API not accessible: {e}")
        return False

def test_api_docs():
    """Test API documentation"""
    print("\n2️⃣ Testing API Documentation...")
    try:
        response = requests.get(f"{API_URL}/docs")
        if response.status_code == 200:
            print(f"   ✅ API docs accessible")
            print(f"   📚 Documentation: {API_URL}/docs")
            return True
        else:
            print(f"   ❌ API docs not accessible (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def test_trial_signup():
    """Test trial signup"""
    print("\n3️⃣ Testing Trial Signup...")
    
    signup_data = {
        "email": test_email,
        "password": test_password,
        "organization_name": test_org,
        "full_name": "Test User",
        "phone": "+1234567890"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/trial/signup",
            json=signup_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Signup successful!")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Trial ends: {data.get('trial_end_date')}")
            return data.get('access_token')
        else:
            print(f"   ❌ Signup failed (Status: {response.status_code})")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_login(token=None):
    """Test login"""
    print("\n4️⃣ Testing Login...")
    
    login_data = {
        "username": test_email,  # FastAPI OAuth2 expects 'username'
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data=login_data,  # Form data for OAuth2
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token type: {data.get('token_type')}")
            return data.get('access_token')
        else:
            print(f"   ❌ Login failed (Status: {response.status_code})")
            print(f"   Error: {response.text}")
            return token  # Return existing token if login fails
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return token

def test_protected_endpoints(token):
    """Test protected API endpoints"""
    print("\n5️⃣ Testing Protected Endpoints...")
    
    if not token:
        print("   ⚠️ No token available, skipping protected endpoints")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("GET", "/api/trial/status", "Trial Status"),
        ("GET", "/api/dashboard/overview", "Dashboard Overview"),
        ("GET", "/api/compliance/requirements", "Compliance Requirements")
    ]
    
    for method, endpoint, name in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            
            print(f"   {name}: {response.status_code}")
            if response.status_code == 200:
                print(f"      ✅ Data: {json.dumps(response.json(), indent=9)[:100]}...")
        except Exception as e:
            print(f"   {name}: ❌ Failed - {e}")

def test_frontend_pages():
    """Test frontend pages"""
    print("\n6️⃣ Testing Frontend Pages...")
    
    pages = [
        ("/", "Homepage"),
        ("/login", "Login page"),
        ("/signup", "Signup page"),
        ("/dashboard", "Dashboard"),
        ("/pricing", "Pricing page"),
        ("/features", "Features page")
    ]
    
    for path, name in pages:
        try:
            response = requests.get(f"{FRONTEND_URL}{path}", allow_redirects=True)
            if response.status_code == 200:
                print(f"   ✅ {name} accessible")
            else:
                print(f"   ⚠️ {name} returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name} error: {e}")

def test_stripe_checkout(token):
    """Test Stripe checkout creation"""
    print("\n7️⃣ Testing Stripe Checkout...")
    
    if not token:
        print("   ⚠️ No token available, skipping checkout test")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different price IDs
    price_tests = [
        ("price_1Q0uElRx59MW7hVBHedTxnRw", "Monthly ($995)"),
        ("price_1Q0uGXRx59MW7hVB8BUcNcrB", "Annual ($10k)"),
        ("price_1Q0uIKRx59MW7hVBEiUMXhka", "One-time ($299)")
    ]
    
    for price_id, name in price_tests:
        try:
            response = requests.post(
                f"{API_URL}/api/checkout/create-session",
                json={"price_id": price_id},
                headers={**headers, "Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {name} checkout created")
                print(f"      URL: {data.get('url', 'N/A')[:50]}...")
            else:
                print(f"   ❌ {name} checkout failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name} error: {e}")

# Run all tests
print("\n" + "=" * 50)
print("Starting Complete Platform Test...")
print("=" * 50)

# Test API
api_healthy = test_api_health()
if api_healthy:
    test_api_docs()
    
    # Test authentication flow
    token = test_trial_signup()
    if not token:
        token = test_login()
    
    # Test protected endpoints
    test_protected_endpoints(token)
    
    # Test Stripe integration
    test_stripe_checkout(token)
else:
    print("\n⚠️ API not healthy, skipping API tests")

# Test frontend
test_frontend_pages()

print("\n" + "=" * 50)
print("✅ Platform Test Complete!")
print("=" * 50)

print("\n📊 Summary:")
print(f"   - API URL: {API_URL}")
print(f"   - Frontend URL: {FRONTEND_URL}")
print(f"   - Test user: {test_email}")

print("\n🎯 Next Steps:")
print("1. Check Stripe dashboard for test transactions")
print("2. Verify email delivery in Postmark")
print("3. Test the actual login flow in browser")
print("4. Monitor Railway and Vercel logs")
