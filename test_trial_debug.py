#!/usr/bin/env python3
"""Debug trial signup issue"""

import requests
import json

API_URL = "https://api.mapmystandards.ai"

print("🔍 Debugging Trial Signup 500 Error")
print("=" * 50)

# Check the trial router schema
print("\n1. Checking OpenAPI schema for trial endpoints...")
openapi_response = requests.get(f"{API_URL}/openapi.json")
if openapi_response.status_code == 200:
    openapi = openapi_response.json()
    trial_signup = openapi["paths"].get("/api/trial/signup", {}).get("post", {})
    if trial_signup:
        print("Trial signup schema:")
        request_body = trial_signup.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        if "$ref" in request_body:
            # Get the referenced schema
            ref_path = request_body["$ref"].split("/")[-1]
            schema = openapi["components"]["schemas"].get(ref_path, {})
            print(f"  Model: {ref_path}")
            print("  Required fields:", schema.get("required", []))
            print("  Properties:")
            for prop, details in schema.get("properties", {}).items():
                print(f"    - {prop}: {details.get('type', 'unknown')}")
        else:
            print("  Schema:", json.dumps(request_body, indent=4))

# Try with exact required fields
print("\n2. Testing with exact required fields...")
required_data = {
    "email": "test_exact@example.com",
    "password": "TestPassword123!",
    "organization_name": "Test Organization"
}

response = requests.post(
    f"{API_URL}/api/trial/signup",
    json=required_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {response.text}")

# Check if it's a Stripe issue by testing tier endpoints
print("\n3. Testing tier management endpoints...")
tier_status = requests.get(f"{API_URL}/api/tier/status/test@example.com")
print(f"Tier status check: {tier_status.status_code}")
if tier_status.status_code == 200:
    print(f"Response: {tier_status.json()}")

# Check auth endpoints with correct path
print("\n4. Testing auth endpoints...")
auth_endpoints = [
    ("/auth/register-trial", "POST", {"email": "auth_test@example.com", "password": "Test123!", "institution_name": "Test Inst"}),
    ("/auth/login", "POST", {"username": "test@example.com", "password": "test123"})
]

for path, method, data in auth_endpoints:
    if method == "POST":
        # Try both content types
        print(f"\n{path}:")
        
        # JSON
        r1 = requests.post(f"{API_URL}{path}", json=data, headers={"Content-Type": "application/json"})
        print(f"  JSON: {r1.status_code} - {r1.text[:100]}")
        
        # Form data
        r2 = requests.post(f"{API_URL}{path}", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        print(f"  Form: {r2.status_code} - {r2.text[:100]}")

print("\n" + "=" * 50)
print("Possible issues:")
print("1. Database connection not configured in Railway")
print("2. Stripe API keys not set in environment variables")
print("3. Email service (Postmark) not configured")
print("4. Missing required fields in request")
