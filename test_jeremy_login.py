#!/usr/bin/env python3
"""
Test Jeremy's login and check user data
"""

import requests
import json

# Configuration
API_BASE_URL = "https://api.mapmystandards.ai"
EMAIL = "jeremy.estrella@gmail.com"
PASSWORD = "Ipo4Eva45*"

print("🔐 Testing Jeremy's Login\n")

# Test login
login_data = {
    "email": EMAIL,
    "password": PASSWORD
}

print(f"Logging in as: {EMAIL}")

response = requests.post(
    f"{API_BASE_URL}/api/auth/login",
    json=login_data,
    headers={"Content-Type": "application/json"}
)

print(f"\nResponse Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n✅ Login Successful!")
    
    # Display user information
    if 'user' in data:
        user = data['user']
        print("\n📋 User Information:")
        print(f"  - Email: {user.get('email', 'N/A')}")
        print(f"  - Name: {user.get('name', 'N/A')}")
        print(f"  - Institution: {user.get('institution', 'N/A')}")
        print(f"  - Role: {user.get('role', 'N/A')}")
        print(f"  - Onboarding Completed: {user.get('onboarding_completed', False)}")
        print(f"  - Primary Accreditor: {user.get('primary_accreditor', 'N/A')}")
        
        # Check subscription status
        if 'subscription' in user:
            sub = user['subscription']
            print(f"\n💳 Subscription:")
            print(f"  - Status: {sub.get('status', 'N/A')}")
            print(f"  - Plan: {sub.get('plan', 'N/A')}")
    
    # Token info
    if 'access_token' in data:
        token = data['access_token']
        print(f"\n🎫 Access Token: {token[:50]}...")
        
        # Test token validation
        print("\n🔍 Testing token validation...")
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Try to get user settings
        settings_response = requests.get(
            f"{API_BASE_URL}/api/user/intelligence-simple/settings",
            headers=auth_headers
        )
        
        print(f"Settings endpoint status: {settings_response.status_code}")
        if settings_response.status_code == 200:
            settings = settings_response.json()
            print("✅ Token is valid and settings retrieved")
            print(f"Organization: {settings.get('organization', 'Not set')}")
            print(f"Primary Accreditor: {settings.get('primary_accreditor', 'Not set')}")
        else:
            print(f"❌ Settings endpoint failed: {settings_response.text}")
            
else:
    print(f"\n❌ Login Failed: {response.text}")

print("\n" + "="*50)