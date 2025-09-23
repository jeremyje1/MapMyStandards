#!/usr/bin/env python3
"""
Test the live platform with Jeremy's credentials
"""

import requests
import json
from datetime import datetime

print("🌐 Testing Live Platform")
print(f"Time: {datetime.now()}")
print("="*50 + "\n")

# Test login page
login_url = "https://platform.mapmystandards.ai/login-enhanced-v2.html"
print(f"1. Checking login page: {login_url}")
response = requests.get(login_url)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    # Check if demo credentials are removed
    if "testuser@example.com" in response.text:
        print("   ❌ Demo credentials still visible")
    else:
        print("   ✅ Demo credentials removed")

# Test authentication
print("\n2. Testing authentication API")
auth_data = {
    "email": "jeremy.estrella@gmail.com", 
    "password": "Ipo4Eva45*"
}

auth_response = requests.post(
    "https://api.mapmystandards.ai/api/auth/login",
    json=auth_data,
    headers={"Content-Type": "application/json"}
)

print(f"   Status: {auth_response.status_code}")
if auth_response.status_code == 200:
    print("   ✅ Authentication successful!")
    data = auth_response.json()
    token = data.get('access_token', '')
    
    # Test protected endpoints
    print("\n3. Testing protected endpoints with token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/api/user/intelligence-simple/settings", "User Settings"),
        ("/api/user/me", "User Profile"),
        ("/api/documents", "Documents")
    ]
    
    for endpoint, name in endpoints:
        url = f"https://api.mapmystandards.ai{endpoint}"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"   - {name}: {resp.status_code} {'✅' if resp.status_code == 200 else '❌'}")
        except Exception as e:
            print(f"   - {name}: Error - {str(e)}")

# Check all enhanced pages
print("\n4. Checking enhanced pages")
pages = [
    "dashboard-enhanced.html",
    "standards-graph-enhanced.html", 
    "compliance-dashboard-enhanced.html",
    "reports-enhanced.html",
    "organizational-enhanced.html",
    "settings-enhanced.html",
    "about-enhanced.html",
    "contact-enhanced.html"
]

all_good = True
for page in pages:
    url = f"https://platform.mapmystandards.ai/{page}"
    resp = requests.head(url)
    status = "✅" if resp.status_code == 200 else "❌"
    if resp.status_code != 200:
        all_good = False
    print(f"   - {page}: {status}")

print(f"\n{'='*50}")
print("Summary:")
print(f"- Login page updated: {'✅' if 'testuser@example.com' not in response.text else '❌'}")
print(f"- Authentication working: {'✅' if auth_response.status_code == 200 else '❌'}")
print(f"- All pages accessible: {'✅' if all_good else '❌'}")
print(f"{'='*50}")