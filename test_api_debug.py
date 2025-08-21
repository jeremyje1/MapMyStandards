#!/usr/bin/env python3
"""Debug API issues"""

import requests
import json

API_URL = "https://api.mapmystandards.ai"

print("🔍 Debugging API Issues")
print("=" * 50)

# Test trial signup with minimal data
print("\n1. Testing Trial Signup with minimal data...")
signup_data = {
    "email": "test@example.com",
    "password": "Test123!",
    "organization_name": "Test Org"
}

response = requests.post(
    f"{API_URL}/api/trial/signup",
    json=signup_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {response.text}")

# Test with all fields
print("\n2. Testing Trial Signup with all fields...")
signup_data_full = {
    "email": "test2@example.com",
    "password": "Test123!",
    "organization_name": "Test University",
    "full_name": "Test User",
    "phone": "+1234567890"
}

response2 = requests.post(
    f"{API_URL}/api/trial/signup",
    json=signup_data_full,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response2.status_code}")
print(f"Response: {response2.text[:500]}")

# Test login endpoint path
print("\n3. Testing different login paths...")
login_paths = [
    "/api/auth/login",
    "/api/login",
    "/auth/login",
    "/login"
]

login_data = {
    "username": "test@example.com",
    "password": "Test123!"
}

for path in login_paths:
    try:
        # Try form data first (OAuth2 style)
        r1 = requests.post(
            f"{API_URL}{path}",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"\n{path} (form data): {r1.status_code}")
        
        # Try JSON
        r2 = requests.post(
            f"{API_URL}{path}",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"{path} (json): {r2.status_code}")
        
        if r1.status_code == 200 or r2.status_code == 200:
            print(f"✅ Found working login endpoint: {path}")
            break
    except Exception as e:
        print(f"{path}: Error - {str(e)[:50]}")

# Check what's in the root
print("\n4. Checking API root...")
root_response = requests.get(API_URL)
print(f"Root status: {root_response.status_code}")
if root_response.status_code == 200:
    print(f"Root response: {root_response.text[:200]}...")

# Check OpenAPI schema
print("\n5. Checking OpenAPI schema...")
openapi_response = requests.get(f"{API_URL}/openapi.json")
if openapi_response.status_code == 200:
    openapi = openapi_response.json()
    print("Available paths:")
    for path in sorted(openapi.get("paths", {}).keys()):
        methods = list(openapi["paths"][path].keys())
        print(f"  {path}: {methods}")
