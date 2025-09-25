#!/usr/bin/env python3
"""Test if the deployment includes our UUID changes"""

import requests
import json

API_BASE = "https://api.mapmystandards.ai"

print("Testing if deployment includes UUID changes")
print("=" * 60)

# Test the verify-token endpoint to see if it returns user_id
print("\n1. Testing /api/auth/verify-token endpoint...")

# First, let's try to login and get a fresh token
login_data = {
    "email": "test@example.com",  # This will fail but we can see the response
    "password": "test123"
}

try:
    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
    print(f"   Login attempt status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.text[:200]}...")
except Exception as e:
    print(f"   Error: {e}")

# Test if the new endpoints respond
print("\n2. Testing endpoint availability...")
test_endpoints = [
    ("GET", "/api/user/intelligence-simple/documents/list"),
    ("POST", "/api/user/intelligence-simple/documents/test-id/analyze"),
    ("GET", "/api/user/intelligence-simple/uploads/test-id"),
]

headers = {
    "Authorization": "Bearer invalid-token",  # Will fail auth but shows endpoint exists
    "Content-Type": "application/json"
}

for method, endpoint in test_endpoints:
    url = f"{API_BASE}{endpoint}"
    print(f"\n   {method} {endpoint}")
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json={})
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            # Check if response mentions "Invalid or expired token" (our new code)
            if "Invalid or expired token" in response.text:
                print("   ✓ Using our code (correct error message)")
            else:
                print(f"   ? Response: {response.text[:100]}")
        elif response.status_code == 500:
            print(f"   ✗ Server error: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n3. Checking API health...")
response = requests.get(f"{API_BASE}/health")
print(f"   Health status: {response.status_code}")

print("\n" + "=" * 60)
print("If you see 500 errors above, the new code may not be deployed yet.")
print("Railway can take 2-5 minutes to build and deploy after push.")