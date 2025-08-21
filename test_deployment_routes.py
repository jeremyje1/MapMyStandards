#!/usr/bin/env python3
"""Test to verify which routes are actually available on the deployment"""

import requests
import json

BASE_URL = "https://mapmystandards-prod-production.up.railway.app"

print("🔍 Testing Railway Deployment Routes")
print("=" * 50)
print(f"Base URL: {BASE_URL}\n")

# Test if we can get the OpenAPI schema
print("1. Checking for OpenAPI schema...")
routes_to_check = [
    "/openapi.json",
    "/api/openapi.json", 
    "/api/v1/openapi.json",
    "/docs",
    "/api/docs",
    "/redoc"
]

for route in routes_to_check:
    response = requests.get(f"{BASE_URL}{route}")
    print(f"   {route}: {response.status_code}")
    if response.status_code == 200 and route.endswith('.json'):
        try:
            schema = response.json()
            print(f"   ✅ Found OpenAPI schema! Analyzing routes...")
            
            # Extract paths from OpenAPI schema
            if 'paths' in schema:
                print("\n   Available API endpoints:")
                for path in sorted(schema['paths'].keys()):
                    methods = list(schema['paths'][path].keys())
                    print(f"   - {path} [{', '.join(methods).upper()}]")
                break
        except:
            pass

print("\n2. Testing specific endpoints...")
# Based on your router configurations
test_endpoints = [
    ("GET", "/health", None),
    ("POST", "/api/trial/signup", {"email": "test@example.com", "password": "test123", "organization_name": "Test"}),
    ("POST", "/trial/signup", {"email": "test@example.com", "password": "test123", "organization_name": "Test"}),
    ("POST", "/auth/login", {"username": "test@example.com", "password": "test123"}),
    ("POST", "/api/auth/login", {"username": "test@example.com", "password": "test123"}),
    ("GET", "/api/trial/status/test@example.com", None),
    ("GET", "/trial/status/test@example.com", None),
]

for method, endpoint, data in test_endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        print(f"   {method:4} {endpoint:40} -> {response.status_code}")
        
        if response.status_code not in [404, 405]:
            print(f"        Response: {response.text[:100]}...")
    except Exception as e:
        print(f"   {method:4} {endpoint:40} -> ERROR: {str(e)[:30]}")

print("\n3. Checking what's actually running...")
# Try to access root and see what we get
response = requests.get(BASE_URL)
if response.status_code == 200:
    content_type = response.headers.get('content-type', '')
    print(f"   Root (/) returns: {content_type}")
    if 'html' in content_type:
        print("   ✅ Serving HTML files")
    if len(response.text) > 0:
        print(f"   Content preview: {response.text[:200]}...")
