#!/usr/bin/env python3
"""Test working authentication flow"""

import requests
import json
import time

API_URL = "https://api.mapmystandards.ai"

print("🧪 Testing Working Authentication Flow")
print("=" * 50)

# 1. Test login with correct path
print("\n1️⃣ Testing Login at /auth/login...")
login_data = {
    "username": "admin@mapmystandards.ai",  # Try a known user
    "password": "admin123"
}

# Try form data (OAuth2 style)
response = requests.post(
    f"{API_URL}/auth/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Login successful!")
    print(f"Response: {json.dumps(data, indent=2)}")
    token = data.get("access_token")
else:
    print(f"Response: {response.text}")
    token = None

# 2. Try registration
print("\n2️⃣ Testing Registration at /auth/register-trial...")
register_data = {
    "email": f"newuser_{int(time.time())}@example.com",
    "password": "Test123!",
    "institution_name": "Test University",
    "full_name": "Test User"
}

response = requests.post(
    f"{API_URL}/auth/register-trial",
    json=register_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# 3. Test the trial signup endpoint to see the error
print("\n3️⃣ Debugging Trial Signup Error...")
print("Checking required fields...")

# Try with minimal data
minimal_data = {
    "email": f"trial_{int(time.time())}@example.com",
    "password": "Test123!"
}

response = requests.post(
    f"{API_URL}/api/trial/signup",
    json=minimal_data,
    headers={"Content-Type": "application/json"}
)

print(f"Minimal data status: {response.status_code}")
print(f"Response: {response.text}")

# Check if we can get more error details
print("\n4️⃣ Checking server configuration...")

# Test tier management health (another endpoint that should work)
tier_health = requests.get(f"{API_URL}/api/tier/health")
print(f"Tier health status: {tier_health.status_code}")
if tier_health.status_code == 200:
    print(f"Tier health response: {tier_health.json()}")

# Try to access a protected endpoint with a fake token to see error format
print("\n5️⃣ Testing error responses...")
fake_headers = {"Authorization": "Bearer fake-token"}
protected_response = requests.get(
    f"{API_URL}/api/dashboard/overview",
    headers=fake_headers
)
print(f"Protected endpoint status: {protected_response.status_code}")
print(f"Protected endpoint response: {protected_response.text[:200]}")

print("\n" + "=" * 50)
print("Summary:")
print("- Auth endpoints are at /auth/* not /api/auth/*")
print("- Trial signup endpoint exists but returns 500")
print("- Server is running FastAPI with proper routes")
print("- Need to check Railway logs for the 500 error details")
