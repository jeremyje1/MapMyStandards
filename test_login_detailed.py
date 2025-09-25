#!/usr/bin/env python3
"""Test login with detailed response analysis"""

import requests
import json

API_BASE = "https://api.mapmystandards.ai"

# Test credentials
EMAIL = "jeremy.estrella@gmail.com"
PASSWORD = "Ipo4Eva45*"

print("=" * 60)
print("Detailed Login Test")
print("=" * 60)

# Test login
print("\nTesting login endpoint...")
login_data = {
    "email": EMAIL,
    "password": PASSWORD,
    "remember": True
}

response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"\nResponse body:")
try:
    response_json = response.json()
    print(json.dumps(response_json, indent=2))
except:
    print(response.text)

# Also check cookies
print(f"\nCookies: {response.cookies}")

# Try the db login endpoint
print("\n" + "=" * 60)
print("Testing /api/auth/db/login endpoint...")
response = requests.post(f"{API_BASE}/api/auth/db/login", json=login_data)
print(f"Status Code: {response.status_code}")
print(f"\nResponse body:")
try:
    response_json = response.json()
    print(json.dumps(response_json, indent=2))
    
    # If successful, extract token
    if response.status_code == 200 and "access_token" in response_json:
        token = response_json["access_token"]
        print(f"\n✓ Got token!")
        
        # Decode token
        import base64
        parts = token.split('.')
        if len(parts) == 3:
            payload = base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
            payload_dict = json.loads(payload)
            print(f"\nToken payload:")
            print(json.dumps(payload_dict, indent=2))
except:
    print(response.text)

# Try simple auth login
print("\n" + "=" * 60)
print("Testing /api/auth/simple/login endpoint...")
response = requests.post(f"{API_BASE}/api/auth/simple/login", json=login_data)
print(f"Status Code: {response.status_code}")
print(f"\nResponse body:")
try:
    response_json = response.json()
    print(json.dumps(response_json, indent=2))
except:
    print(response.text)