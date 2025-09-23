#!/usr/bin/env python3
"""
Discover working API endpoints on production
"""

import requests
import json

# Configuration
BASE_URL = "https://api.mapmystandards.ai"
TEST_USER = {
    "email": "jeremy.estrella@gmail.com", 
    "password": "Ipo4Eva45*"
}

def test_auth_endpoints():
    """Test different auth endpoint variations"""
    print("Testing Authentication Endpoints...")
    
    auth_urls = [
        f"{BASE_URL}/api/auth/login",
        f"{BASE_URL}/auth/login",
        f"{BASE_URL}/api/auth/simple/login",
        f"{BASE_URL}/api/auth/complete/login",
        f"{BASE_URL}/api/auth/session/login",
        f"{BASE_URL}/login"
    ]
    
    for url in auth_urls:
        try:
            response = requests.post(url, json=TEST_USER)
            print(f"\n{url}:")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                return data.get("access_token") or data.get("token")
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def test_user_endpoints(token):
    """Test user-related endpoints"""
    print("\n\nTesting User Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    user_urls = [
        f"{BASE_URL}/api/users/me",
        f"{BASE_URL}/api/user/me", 
        f"{BASE_URL}/api/user/profile",
        f"{BASE_URL}/api/user/profile/",
        f"{BASE_URL}/api/auth/me",
        f"{BASE_URL}/api/auth/simple/me",
        f"{BASE_URL}/api/auth/complete/me",
        f"{BASE_URL}/me"
    ]
    
    for url in user_urls:
        try:
            response = requests.get(url, headers=headers)
            print(f"\n{url}:")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Response: {json.dumps(response.json(), indent=2)[:200]}...")
        except Exception as e:
            print(f"  Error: {e}")

def test_settings_endpoints(token):
    """Test settings endpoints"""
    print("\n\nTesting Settings Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    settings_urls = [
        f"{BASE_URL}/api/users/settings",
        f"{BASE_URL}/api/user/settings",
        f"{BASE_URL}/api/settings",
        f"{BASE_URL}/api/auth/simple/settings",
        f"{BASE_URL}/api/auth/complete/settings"
    ]
    
    for url in settings_urls:
        try:
            response = requests.get(url, headers=headers) 
            print(f"\n{url}:")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Response: {json.dumps(response.json(), indent=2)[:200]}...")
        except Exception as e:
            print(f"  Error: {e}")

def test_document_endpoints(token):
    """Test document-related endpoints"""
    print("\n\nTesting Document Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    doc_urls = [
        f"{BASE_URL}/api/documents",
        f"{BASE_URL}/api/documents/",
        f"{BASE_URL}/api/v1/documents",
        f"{BASE_URL}/api/documents/list",
        f"{BASE_URL}/api/upload",
        f"{BASE_URL}/api/v1/upload"
    ]
    
    for url in doc_urls:
        try:
            response = requests.get(url, headers=headers)
            print(f"\n{url}:")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Response: {json.dumps(response.json(), indent=2)[:200]}...")
        except Exception as e:
            print(f"  Error: {e}")

def main():
    print("="*60)
    print("API ENDPOINT DISCOVERY")
    print("="*60)
    
    # Test authentication
    token = test_auth_endpoints()
    
    if token:
        print(f"\n✅ Authentication successful! Token: {token[:20]}...")
        
        # Test other endpoints
        test_user_endpoints(token)
        test_settings_endpoints(token) 
        test_document_endpoints(token)
    else:
        print("\n❌ Could not authenticate - cannot test protected endpoints")

if __name__ == "__main__":
    main()