#!/usr/bin/env python3
"""Quick API test with known working token"""
import requests
import os
import json

# Use the token we know worked before
WORKING_TOKEN = os.getenv("TEST_JWT_TOKEN", "")

def test_api():
    """Test the dashboard API endpoint"""
    url = "http://localhost:8000/api/user/intelligence-simple/dashboard/overview"
    headers = {
        "Authorization": f"Bearer {WORKING_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing API endpoint...")
    print(f"URL: {url}")
    print(f"Token: {WORKING_TOKEN[:50]}...")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS! API is working")
            print("Response:", response.json())
        else:
            print("❌ FAILED!")
            print("Response text:", response.text[:500])
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
