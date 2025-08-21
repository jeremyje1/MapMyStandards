#!/usr/bin/env python3
"""
Customer Flow Testing Script
Tests all critical customer journeys on the MapMyStandards platform
"""

import requests
import json
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin

# Configuration
PLATFORM_URL = "https://platform.mapmystandards.ai"
API_URL = "https://api.mapmystandards.ai"  # This appears to be wrong
TIMEOUT = 10

class CustomerFlowTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "status": status,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_url_accessibility(self, url: str, expected_status: int = 200) -> bool:
        """Test if a URL is accessible"""
        try:
            response = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            return response.status_code == expected_status
        except Exception as e:
            return False
    
    def test_navigation_links(self):
        """Test all navigation links from the homepage"""
        print("\n🔍 Testing Navigation Links...")
        
        nav_links = [
            ("Homepage", f"{PLATFORM_URL}/", 200),
            ("API Root", f"{PLATFORM_URL}/api", 200),
            ("Health Check", f"{PLATFORM_URL}/health", 200),
            ("Login Page", f"{PLATFORM_URL}/login", 200),
            ("Dashboard", f"{PLATFORM_URL}/dashboard", 200),
            ("Services (WordPress)", "https://mapmystandards.ai/services/", 200),
            ("About (WordPress)", "https://mapmystandards.ai/about/", 200),
            ("Contact (WordPress)", "https://mapmystandards.ai/contact/", 200),
        ]
        
        for name, url, expected in nav_links:
            passed = self.test_url_accessibility(url, expected)
            self.log_result(f"Navigation: {name}", passed, f"URL: {url}")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        # Test documented API endpoints
        api_endpoints = [
            ("API Status", f"{API_URL}/status", 200),
            ("API Docs", f"{API_URL}/docs", 200),
            ("Auth Login (Wrong)", f"{API_URL}/auth/login", 405),  # GET not allowed
            ("Platform Auth Login", f"{PLATFORM_URL}/auth/login", 405),  # Correct endpoint
            ("Upload Endpoint", f"{API_URL}/upload", 200),
        ]
        
        for name, url, expected in api_endpoints:
            passed = self.test_url_accessibility(url, expected)
            self.log_result(f"API: {name}", passed, f"URL: {url}")
    
    def test_authentication_flow(self):
        """Test authentication flow"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test login endpoint
        login_data = {
            "email": "test@example.com",
            "password": "testpassword",
            "remember": False
        }
        
        # Try wrong endpoint first (as the frontend does)
        try:
            response = self.session.post(
                f"{API_URL}/auth/login",
                json=login_data,
                timeout=TIMEOUT
            )
            self.log_result(
                "Auth: Wrong API endpoint", 
                False, 
                f"Frontend uses wrong endpoint - Status: {response.status_code}"
            )
        except Exception as e:
            self.log_result("Auth: Wrong API endpoint", False, f"Error: {str(e)}")
        
        # Try correct endpoint
        try:
            response = self.session.post(
                f"{PLATFORM_URL}/auth/login",
                json=login_data,
                timeout=TIMEOUT
            )
            success = response.status_code in [200, 401, 403]  # Any auth response is "working"
            self.log_result(
                "Auth: Correct platform endpoint", 
                success,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_result("Auth: Correct platform endpoint", False, f"Error: {str(e)}")
    
    def test_customer_features(self):
        """Test advertised customer features"""
        print("\n📊 Testing Customer Features...")
        
        features = [
            ("Evidence Upload", f"{PLATFORM_URL}/upload", "Upload interface"),
            ("Standards Browser", f"{PLATFORM_URL}/standards", "Standards listing"),
            ("Gap Analysis", f"{PLATFORM_URL}/analysis", "Analysis dashboard"),
            ("Compliance Tracking", f"{PLATFORM_URL}/compliance", "Compliance view"),
            ("Document Management", f"{PLATFORM_URL}/documents", "Document library"),
        ]
        
        for name, url, description in features:
            exists = self.test_url_accessibility(url)
            self.log_result(f"Feature: {name}", exists, f"{description} at {url}")
    
    def test_static_assets(self):
        """Test static assets and resources"""
        print("\n🎨 Testing Static Assets...")
        
        assets = [
            ("Logo Image", "https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png"),
            ("Stylesheet", f"{PLATFORM_URL}/assets/styles.css"),
            ("Login Page", f"{PLATFORM_URL}/web/login.html"),
            ("Dashboard Page", f"{PLATFORM_URL}/web/dashboard.html"),
        ]
        
        for name, url in assets:
            exists = self.test_url_accessibility(url)
            self.log_result(f"Asset: {name}", exists, url)
    
    def test_user_journey(self):
        """Test complete user journey"""
        print("\n🚶 Testing Complete User Journey...")
        
        # 1. Visit homepage
        homepage_ok = self.test_url_accessibility(PLATFORM_URL)
        self.log_result("Journey: Visit homepage", homepage_ok)
        
        # 2. Navigate to login
        login_page_ok = self.test_url_accessibility(f"{PLATFORM_URL}/login")
        self.log_result("Journey: Navigate to login", login_page_ok)
        
        # 3. Attempt login (will fail but should get response)
        try:
            login_response = self.session.post(
                f"{PLATFORM_URL}/auth/login",
                json={"email": "test@test.com", "password": "test"},
                timeout=TIMEOUT
            )
            login_works = login_response.status_code in [200, 401, 403]
            self.log_result("Journey: Login attempt", login_works, f"Status: {login_response.status_code}")
        except:
            self.log_result("Journey: Login attempt", False, "Login endpoint error")
        
        # 4. Access dashboard (should redirect to login)
        dashboard_accessible = self.test_url_accessibility(f"{PLATFORM_URL}/dashboard")
        self.log_result("Journey: Access dashboard", dashboard_accessible)
    
    def generate_report(self):
        """Generate summary report"""
        print("\n" + "="*60)
        print("CUSTOMER FLOW TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n📋 Recommendations:")
        print("1. Update all navigation links to use platform.mapmystandards.ai")
        print("2. Fix API endpoint references in frontend code")
        print("3. Create missing feature pages (upload, standards, etc.)")
        print("4. Implement proper authentication flow")
        print("5. Add user onboarding and help documentation")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": self.results
        }

def main():
    """Run all customer flow tests"""
    print("🧪 MapMyStandards Customer Flow Testing")
    print("Testing platform:", PLATFORM_URL)
    print("="*60)
    
    tester = CustomerFlowTester()
    
    # Run all tests
    tester.test_navigation_links()
    tester.test_api_endpoints()
    tester.test_authentication_flow()
    tester.test_customer_features()
    tester.test_static_assets()
    tester.test_user_journey()
    
    # Generate report
    report = tester.generate_report()
    
    # Save results
    with open("customer_flow_test_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Test results saved to customer_flow_test_results.json")
    
    # Exit with error code if tests failed
    exit(0 if report["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
