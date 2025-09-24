#!/usr/bin/env python3
"""
Test actual endpoints the frontend is using
"""

import requests
import json

BASE_URL = "https://api.mapmystandards.ai"
FRONTEND_URL = "https://platform.mapmystandards.ai"

# First, get a real token
print("1. Getting authentication token...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "jeremy.estrella@gmail.com",
        "password": "Ipo4Eva45*"
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Got token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# Test endpoints that the frontend actually uses
print("\n2. Testing frontend-used endpoints...")

endpoints = [
    ("User Settings (intelligence-simple)", "GET", "/api/user/intelligence-simple/settings"),
    ("User Profile", "GET", "/api/auth/me"),
    ("Standards Selection", "GET", "/api/user/intelligence-simple/standards/selection/load"),
    ("Dashboard Overview", "GET", "/api/dashboard/overview"),
    ("Documents List", "GET", "/api/v1/upload"),
]

for name, method, endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, json={}, timeout=5)
        
        status = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status} {name}: {response.status_code}")
        
        if response.status_code == 200:
            # Show a bit of the response
            data = response.json()
            print(f"   Response preview: {json.dumps(data, indent=2)[:100]}...")
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")

print("\n3. Testing what the dashboard actually calls...")
# Simulate what the dashboard does
dashboard_response = requests.get(
    f"{FRONTEND_URL}/dashboard-enhanced.html",
    headers={"Cookie": f"token={token}"}  # Frontend might use cookies
)
print(f"Dashboard HTML loads: {dashboard_response.status_code}")

print("\n✅ Analysis complete!")
print("The frontend is using the intelligence-simple endpoints, not the simple endpoints we created.")