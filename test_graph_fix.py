#!/usr/bin/env python3
"""
Test script to verify the StandardsGraph visualization fix
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if needed
ACCESS_TOKEN = None  # Will be set after login

def test_login():
    """Test user login"""
    global ACCESS_TOKEN
    print("🔐 Testing login...")
    
    # Try with test credentials
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data.get("access_token")
        print("✅ Login successful")
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        return False

def test_graph_endpoint():
    """Test the standards graph API endpoint"""
    print("\n📊 Testing Standards Graph API endpoint...")
    
    if not ACCESS_TOKEN:
        print("❌ No access token available")
        return False
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    # Test with default accreditor
    response = requests.get(f"{BASE_URL}/api/intelligence/standards/graph", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Graph endpoint successful")
        print(f"   - Accreditor: {data.get('accreditor')}")
        print(f"   - Total Standards: {data.get('total_standards')}")
        print(f"   - Relationships: {len(data.get('relationships', []))}")
        print(f"   - Available Accreditors: {data.get('available_accreditors', [])}")
        return True
    else:
        print(f"❌ Graph endpoint failed: {response.status_code}")
        return False

def test_page_load():
    """Test that the standards page loads"""
    print("\n🌐 Testing standards page load...")
    
    response = requests.get(f"{BASE_URL}/standards-modern")
    
    if response.status_code == 200:
        content = response.text
        if "#graph" in content and "graphSection" in content:
            print("✅ Standards page contains graph section")
            return True
        else:
            print("⚠️  Standards page loads but graph section might be missing")
            return False
    else:
        print(f"❌ Standards page failed to load: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print(f"🚀 Testing StandardsGraph Visualization Fix - {datetime.now()}")
    print(f"   Base URL: {BASE_URL}")
    print("="*50)
    
    results = []
    
    # Run tests
    results.append(("Login", test_login()))
    results.append(("Graph API Endpoint", test_graph_endpoint()))
    results.append(("Page Load", test_page_load()))
    
    # Summary
    print("\n📋 Test Summary:")
    print("="*50)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! The StandardsGraph visualization should now work.")
        print("\n📌 To verify manually:")
        print("1. Log into the application")
        print("2. Go to Dashboard")
        print("3. Click 'View Graph' in the Standards Graph section")
        print("4. You should see a graph visualization with options for Network, Tree, or Radial view")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()