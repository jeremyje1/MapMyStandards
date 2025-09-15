#!/usr/bin/env python3
"""
Test script for User Intelligence API endpoints
"""
import requests
import os
import json

# Test configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = os.getenv("TEST_JWT_TOKEN", "")

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_endpoint(endpoint_path, description):
    """Test a single endpoint and print results"""
    url = f"{BASE_URL}{endpoint_path}"
    print(f"\n🧪 Testing: {description}")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success! Response length: {len(str(data))} characters")
                if isinstance(data, dict):
                    print(f"📋 Keys: {list(data.keys())}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Error: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing User Intelligence API Endpoints")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/api/user/intelligence/dashboard/overview", "Original Dashboard Overview"),
        ("/api/user/intelligence-simple/dashboard/overview", "Simple Dashboard Overview"),
        ("/api/user/intelligence-simple/analyze/evidence", "Simple Evidence Analysis"),
        ("/api/user/intelligence-simple/gap-analysis", "Simple Gap Analysis")
    ]
    
    results = []
    for endpoint, description in endpoints:
        success = test_endpoint(endpoint, description)
        results.append((description, success))
    
    print(f"\n🏁 Test Results Summary")
    print("=" * 50)
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n📈 Overall: {success_count}/{len(results)} endpoints working")

if __name__ == "__main__":
    main()
