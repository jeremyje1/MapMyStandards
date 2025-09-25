#!/usr/bin/env python3
"""Test JWT verification with actual tokens from the platform"""

import requests
import json

print("Testing JWT Token Flow")
print("=" * 60)

# Test login to get a fresh token
API_BASE = "https://api.mapmystandards.ai"

# Try to login with test credentials
test_email = "test@example.com"
test_password = "test123"

print(f"\n1. Attempting login with test credentials...")
login_response = requests.post(
    f"{API_BASE}/api/auth/login",
    json={"email": test_email, "password": test_password}
)

print(f"   Status: {login_response.status_code}")
if login_response.status_code == 200:
    data = login_response.json()
    token = data.get("token")
    if token:
        print(f"   Got token: {token[:20]}...")
        
        # Try to use the token
        print("\n2. Testing token with a simple API call...")
        headers = {"Authorization": f"Bearer {token}"}
        test_response = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/documents/list",
            headers=headers
        )
        print(f"   Status: {test_response.status_code}")
        print(f"   Response: {test_response.text[:100]}...")
else:
    print(f"   Response: {login_response.text[:200]}...")

print("\n" + "=" * 60)
print("\nDiagnosis:")
print("If login fails with 401, the test account doesn't exist.")
print("If login succeeds but API calls fail with 401, there's a token verification issue.")
print("\nFor real testing, you need to:")
print("1. Open browser Developer Tools (F12)")
print("2. Go to Network tab")
print("3. Try to use analyze/download feature")
print("4. Look for the failed request")
print("5. Check the Authorization header in the request")
print("6. Copy the Bearer token and test it manually")