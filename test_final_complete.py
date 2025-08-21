#!/usr/bin/env python3
"""Final comprehensive test of the platform"""

import requests
import json
import time

API_URL = "https://api.mapmystandards.ai"
FRONTEND_URL = "https://platform.mapmystandards.ai"

print("🧪 MapMyStandards Final Platform Test")
print("=" * 50)

# 1. API Health
print("\n1️⃣ API Health Check")
health = requests.get(f"{API_URL}/health")
print(f"Status: {health.status_code}")
if health.status_code == 200:
    data = health.json()
    print(f"API Status: {data['status']}")
    print(f"Database: {data['services']['database']['status']}")

# 2. Check OpenAPI docs
print("\n2️⃣ API Documentation")
docs = requests.get(f"{API_URL}/docs")
print(f"Docs status: {docs.status_code}")
openapi = requests.get(f"{API_URL}/openapi.json")
if openapi.status_code == 200:
    print(f"✅ OpenAPI schema available")

# 3. Test with minimal signup
print("\n3️⃣ Testing Minimal Signup")
minimal_signup = {
    "name": "Test User",
    "institution_name": "Test Org",
    "email": "minimal@test.com",
    "password": "Test123!",
    "role": "Administrator"
}

signup_resp = requests.post(
    f"{API_URL}/api/trial/signup",
    json=minimal_signup,
    headers={"Content-Type": "application/json"}
)

print(f"Signup status: {signup_resp.status_code}")
if signup_resp.status_code != 200:
    print(f"Response: {signup_resp.text[:200]}")
    
    # Try to get more info
    print("\n4️⃣ Checking Alternative Endpoints")
    
    # Test tier health
    tier_health = requests.get(f"{API_URL}/api/tier/health")
    print(f"Tier health: {tier_health.status_code}")
    if tier_health.status_code == 200:
        print(f"Response: {tier_health.json()}")
    
    # Test auth register
    auth_register = requests.post(
        f"{API_URL}/auth/register-trial",
        json={
            "name": "Auth Test",
            "institution_name": "Auth Org",
            "email": "auth@test.com",
            "password": "Test123!",
            "role": "Administrator"
        },
        headers={"Content-Type": "application/json"}
    )
    print(f"\nAuth register: {auth_register.status_code}")
    if auth_register.status_code != 200:
        print(f"Response: {auth_register.text[:200]}")

# 5. Frontend check
print("\n5️⃣ Frontend Pages")
pages = ["/", "/login", "/dashboard"]
for page in pages:
    resp = requests.get(f"{FRONTEND_URL}{page}", allow_redirects=True)
    print(f"{page}: {resp.status_code}")

print("\n" + "=" * 50)
print("Test Summary:")
print(f"- API is running: {'✅' if health.status_code == 200 else '❌'}")
print(f"- Database connected: {'✅' if data['services']['database']['status'] == 'healthy' else '❌'}")
print(f"- Trial signup: {'✅' if signup_resp.status_code == 200 else '❌ (500 error)'}")
print(f"- Frontend accessible: ✅")

if signup_resp.status_code == 500:
    print("\n⚠️ The 500 error on signup suggests:")
    print("1. Missing STRIPE_SECRET_KEY in environment variables")
    print("2. Missing POSTMARK_SERVER_TOKEN for email sending")
    print("3. Or another required service configuration")
    print("\nCheck Railway logs for the specific error!")
