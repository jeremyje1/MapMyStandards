#!/usr/bin/env python3
"""
Debug authentication error - test the login endpoint
"""
import requests
import json
import sys

# Configuration
API_BASE_URL = "https://api.mapmystandards.ai"
TEST_EMAIL = "jeremy.estrella@gmail.com"
TEST_PASSWORD = "Ipo4Eva45*"

print("🔍 Debugging Authentication Error\n")
print(f"API URL: {API_BASE_URL}")
print(f"Test User: {TEST_EMAIL}")
print("-" * 50)

# Test 1: Check if API is reachable
print("\n1️⃣ Testing API Health...")
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=10)
    print(f"   Health check: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ API is reachable")
    else:
        print(f"   ❌ API returned: {response.text}")
except Exception as e:
    print(f"   ❌ Cannot reach API: {e}")
    sys.exit(1)

# Test 2: Check login endpoint specifically
print("\n2️⃣ Testing Login Endpoint...")
try:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 500:
        print("\n   ❌ Server Error Details:")
        try:
            error_data = response.json()
            print(f"   {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Raw response: {response.text[:500]}")
            
        print("\n   🔧 Likely causes:")
        print("   - Database connection error")
        print("   - Missing environment variables")
        print("   - Code error in login handler")
        
    elif response.status_code == 200:
        print("   ✅ Login successful!")
        data = response.json()
        print(f"   Token received: {'Yes' if data.get('access_token') else 'No'}")
        
    elif response.status_code == 401:
        print("   ⚠️ Invalid credentials (expected for wrong password)")
        
    elif response.status_code == 404:
        print("   ❌ Login endpoint not found - check API routing")
        
    elif response.status_code == 405:
        print("   ❌ Method not allowed - endpoint expects different HTTP method")
        
    else:
        print(f"   ❓ Unexpected response: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Connection error - API may be down")
except requests.exceptions.Timeout:
    print("   ❌ Request timeout - API is too slow")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try alternative endpoints
print("\n3️⃣ Testing Alternative Auth Endpoints...")
alternatives = [
    "/auth/login",
    "/api/login",
    "/api/auth/signin",
    "/login"
]

for endpoint in alternatives:
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            headers=headers,
            timeout=5
        )
        if response.status_code != 404:
            print(f"   Found endpoint: {endpoint} (Status: {response.status_code})")
    except:
        pass

print("\n" + "=" * 50)
print("📋 RECOMMENDATIONS:")
print("\n1. Check Railway logs:")
print("   railway logs --service backend")
print("\n2. Verify environment variables:")
print("   - DATABASE_URL")
print("   - JWT_SECRET_KEY") 
print("   - Any other required vars")
print("\n3. Test database connection:")
print("   railway run python -c 'from a3e.core.database import engine; print(engine)'")
print("\n4. Check for recent deployments:")
print("   railway status")