#!/usr/bin/env python3
"""Test different API route patterns to find the correct endpoints"""

import requests

BASE_URL = "https://mapmystandards-prod-production.up.railway.app"

# Test different route patterns
routes_to_test = [
    # Documentation routes
    ("/docs", "FastAPI Docs"),
    ("/redoc", "ReDoc"),
    ("/openapi.json", "OpenAPI Schema"),
    
    # API routes with different prefixes
    ("/api/trial/signup", "Trial Signup - /api prefix"),
    ("/trial/signup", "Trial Signup - no prefix"),
    ("/api/v1/trial/signup", "Trial Signup - /api/v1 prefix"),
    
    # Auth routes
    ("/api/auth/login", "Auth Login - /api prefix"),
    ("/auth/login", "Auth Login - no prefix"),
    
    # Health/status routes
    ("/health", "Health check"),
    ("/api/health", "API Health"),
    ("/status", "Status"),
    
    # Root routes
    ("/", "Root"),
    ("/api", "API Root"),
    ("/api/", "API Root with slash"),
]

print("🔍 Testing API Routes on Railway Deployment")
print("=" * 50)
print(f"Base URL: {BASE_URL}\n")

for route, description in routes_to_test:
    url = f"{BASE_URL}{route}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {description:30} - {route:25} [200 OK]")
        elif response.status_code == 404:
            print(f"❌ {description:30} - {route:25} [404 Not Found]")
        else:
            print(f"⚠️  {description:30} - {route:25} [{response.status_code}]")
    except Exception as e:
        print(f"💥 {description:30} - {route:25} [Error: {str(e)[:30]}]")

print("\n" + "=" * 50)
print("Check the main.py file to verify route registration!")
