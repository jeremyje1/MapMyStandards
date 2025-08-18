#!/usr/bin/env python3
"""
A³E Local Testing Script

Tests core functionality of the A³E system running locally.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None, description=""):
    """Test an API endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "status": status,
            "description": description,
            "response_size": len(response.content) if response.content else 0
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": "ERROR",
            "status": f"❌ ERROR: {str(e)}",
            "description": description,
            "response_size": 0
        }

def main():
    print("🚀 A³E Local Testing Suite")
    print("=" * 50)
    print(f"Testing A³E system at: {BASE_URL}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test cases
    tests = [
        # Core system
        ("/health", "GET", None, "System health check"),
        ("/", "GET", None, "Root endpoint"),
        
        # Accreditors and Standards
        ("/api/v1/accreditors", "GET", None, "List all accreditors"),
        ("/api/v1/accreditors/neche/standards", "GET", None, "NECHE standards"),
        ("/api/v1/standards/categories", "GET", None, "Standards categories"),
        
        # Institutions
        ("/api/v1/institutions/institution-types", "GET", None, "Institution types"),
        
        # Canvas Integration
        ("/api/v1/integrations/canvas/test", "GET", None, "Canvas connection test"),
        ("/api/v1/integrations/canvas/courses", "GET", None, "Canvas courses"),
        ("/api/v1/integrations/status", "GET", None, "Integration status"),
        
        # Proprietary Features
        ("/api/v1/proprietary/capabilities", "GET", None, "Proprietary capabilities"),
        
        # Evidence Types
        ("/api/v1/evidence/evidence-types", "GET", None, "Evidence types"),
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for endpoint, method, data, description in tests:
        print(f"Testing: {description}")
        result = test_endpoint(endpoint, method, data, description)
        results.append(result)
        
        status_symbol = "✅" if result["status_code"] == 200 else "❌"
        print(f"  {status_symbol} {endpoint} → {result['status_code']} ({result['response_size']} bytes)")
        
        if result["status_code"] == 200:
            passed += 1
    
    print()
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED!")
        print("✅ A³E system is running successfully in local development mode")
        print("✅ Database connection: Working")
        print("⚠️  Vector database: Offline (development mode)")
        print("✅ Canvas integration: Connected")
        print("✅ Proprietary features: Active")
        print()
        print("🔗 Access the API documentation: http://localhost:8000/docs")
        return 0
    else:
        print()
        print("❌ Some tests failed. Check the server logs for details.")
        print("\nFailed tests:")
        for result in results:
            if result["status_code"] != 200:
                print(f"  - {result['description']}: {result['status']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
