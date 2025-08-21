#!/usr/bin/env python3
"""Test trial signup with correct fields"""

import requests
import json
import time

API_URL = "https://api.mapmystandards.ai"

print("🧪 Testing Trial Signup with Correct Fields")
print("=" * 50)

# Test with all required fields
test_email = f"test_user_{int(time.time())}@example.com"

signup_data = {
    "name": "Test User",  # This was missing!
    "institution_name": "Test University",
    "email": test_email,
    "password": "TestPassword123!",
    "role": "Administrator",  # This was missing!
    "plan": "professional",  # Optional but let's include it
    "phone": "+1234567890",
    "newsletter_opt_in": True
}

print(f"\n1️⃣ Testing Trial Signup with all required fields...")
print(f"Email: {test_email}")

response = requests.post(
    f"{API_URL}/api/trial/signup",
    json=signup_data,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ Signup successful!")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Save the token for further tests
    token = data.get("access_token")
    
    # Test protected endpoints
    if token:
        print("\n2️⃣ Testing protected endpoints with token...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check trial status
        status_response = requests.get(
            f"{API_URL}/api/trial/status/{test_email}",
            headers=headers
        )
        print(f"\nTrial status: {status_response.status_code}")
        if status_response.status_code == 200:
            print(f"Status data: {json.dumps(status_response.json(), indent=2)}")
        
        # Check dashboard
        dashboard_response = requests.get(
            f"{API_URL}/api/dashboard/overview",
            headers=headers
        )
        print(f"\nDashboard: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            print(f"Dashboard data: {json.dumps(dashboard_response.json(), indent=2)[:200]}...")
        
        # Test Stripe checkout
        print("\n3️⃣ Testing Stripe checkout creation...")
        checkout_data = {
            "price_id": "price_1Q0uElRx59MW7hVBHedTxnRw"  # Monthly plan
        }
        
        checkout_response = requests.post(
            f"{API_URL}/api/checkout/create-session",
            json=checkout_data,
            headers={**headers, "Content-Type": "application/json"}
        )
        print(f"Checkout creation: {checkout_response.status_code}")
        if checkout_response.status_code == 200:
            checkout_url = checkout_response.json().get("url")
            print(f"✅ Checkout URL: {checkout_url[:50]}...")
        else:
            print(f"Checkout error: {checkout_response.text}")

else:
    print(f"❌ Signup failed!")
    print(f"Error: {response.text}")
    
    # If it's still 500, it might be database or Stripe configuration
    if response.status_code == 500:
        print("\n⚠️ 500 Error suggests server-side configuration issues:")
        print("1. Check DATABASE_URL is set in Railway")
        print("2. Check STRIPE_SECRET_KEY is set in Railway")
        print("3. Check POSTMARK_SERVER_TOKEN is set in Railway")

# Test auth/register-trial endpoint too
print("\n4️⃣ Testing /auth/register-trial endpoint...")
register_data = {
    "name": "Auth Test User",
    "institution_name": "Auth Test University",
    "email": f"auth_test_{int(time.time())}@example.com",
    "password": "TestPassword123!"
}

register_response = requests.post(
    f"{API_URL}/auth/register-trial",
    json=register_data,
    headers={"Content-Type": "application/json"}
)

print(f"Register status: {register_response.status_code}")
if register_response.status_code == 200:
    print("✅ Registration successful!")
    print(f"Response: {json.dumps(register_response.json(), indent=2)[:200]}...")
else:
    print(f"Register error: {register_response.text[:200]}...")

print("\n" + "=" * 50)
print("Summary:")
print("- Trial signup requires: name, institution_name, email, password, role")
print("- Auth endpoints are at /auth/* not /api/auth/*")
print("- If still getting 500 errors, check Railway environment variables")
