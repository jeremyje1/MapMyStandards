#!/usr/bin/env python3
"""
Complete user flow test - Testing all pages and navigation
Tests the customer experience from login through all features
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://api.mapmystandards.ai"
PLATFORM_URL = "https://platform.mapmystandards.ai"
TEST_EMAIL = "jeremy.estrella@gmail.com"
TEST_PASSWORD = "Ipo4Eva45*"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class UserExperienceTest:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.user_data = {}
        self.test_results = []
        
    async def setup(self):
        """Initialize session"""
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, category: str, test: str, passed: bool, notes: str = ""):
        """Log test result"""
        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        self.test_results.append({
            "category": category,
            "test": test,
            "passed": passed,
            "notes": notes
        })
        print(f"{status} [{category}] {test}")
        if notes:
            print(f"   {YELLOW}→ {notes}{RESET}")
            
    async def test_login(self):
        """Test login flow and get access token"""
        print(f"\n{BLUE}=== Testing Login Flow ==={RESET}")
        
        try:
            # Test login API
            async with self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access_token = data.get("access_token")
                    self.user_data = data.get("user", {})
                    self.log_test("Authentication", "Login API", True, 
                                f"User: {self.user_data.get('email')}")
                    
                    # Check if onboarding data is present
                    if self.user_data.get("onboarding_completed"):
                        self.log_test("Data Persistence", "Onboarding data preserved", True,
                                    f"Institution: {self.user_data.get('institution_name')}")
                    else:
                        self.log_test("Data Persistence", "Onboarding data preserved", False,
                                    "Onboarding not completed or data lost")
                else:
                    error_data = await resp.text()
                    self.log_test("Authentication", "Login API", False, 
                                f"Status {resp.status}: {error_data}")
                    return False
                    
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{BASE_URL}/api/me", 
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log_test("Authentication", "Token validation", True)
                else:
                    self.log_test("Authentication", "Token validation", False, 
                                f"Status {resp.status}")
                    
            return True
            
        except Exception as e:
            self.log_test("Authentication", "Login flow", False, str(e))
            return False
            
    async def test_navigation_links(self):
        """Test all navigation links are accessible"""
        print(f"\n{BLUE}=== Testing Navigation Links ==={RESET}")
        
        pages = [
            ("Dashboard", f"{PLATFORM_URL}/web/dashboard-enhanced.html"),
            ("Upload Evidence", f"{PLATFORM_URL}/web/upload-enhanced.html"),
            ("Standards Graph", f"{PLATFORM_URL}/web/standards-graph-enhanced.html"),
            ("Compliance Dashboard", f"{PLATFORM_URL}/web/compliance-dashboard-enhanced.html"),
            ("Reports", f"{PLATFORM_URL}/web/reports-enhanced.html"),
            ("Organization Chart", f"{PLATFORM_URL}/web/organizational-enhanced.html"),
            ("Settings", f"{PLATFORM_URL}/web/settings-enhanced.html"),
            ("About", f"{PLATFORM_URL}/web/about-enhanced.html"),
            ("Contact", f"{PLATFORM_URL}/web/contact-enhanced.html")
        ]
        
        for page_name, url in pages:
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        self.log_test("Navigation", f"{page_name} page accessible", True)
                    else:
                        self.log_test("Navigation", f"{page_name} page accessible", False,
                                    f"Status {resp.status}")
            except Exception as e:
                self.log_test("Navigation", f"{page_name} page accessible", False, str(e))
                
    async def test_api_endpoints(self):
        """Test all API endpoints for functionality"""
        print(f"\n{BLUE}=== Testing API Endpoints ==={RESET}")
        
        if not self.access_token:
            self.log_test("API", "Endpoints test", False, "No access token")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test settings endpoint
        try:
            async with self.session.get(
                f"{BASE_URL}/api/settings",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    settings = await resp.json()
                    has_accreditor = bool(settings.get("settings", {}).get("primary_accreditor"))
                    self.log_test("API", "Settings endpoint", True,
                                f"Primary accreditor: {settings.get('settings', {}).get('primary_accreditor', 'Not set')}")
                else:
                    self.log_test("API", "Settings endpoint", False, f"Status {resp.status}")
        except Exception as e:
            self.log_test("API", "Settings endpoint", False, str(e))
            
        # Test standards graph data
        try:
            async with self.session.get(
                f"{BASE_URL}/api/standards-graph",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    node_count = len(data.get("nodes", []))
                    self.log_test("API", "Standards graph data", True,
                                f"{node_count} nodes loaded")
                else:
                    self.log_test("API", "Standards graph data", False, f"Status {resp.status}")
        except Exception as e:
            self.log_test("API", "Standards graph data", False, str(e))
            
        # Test org chart
        try:
            async with self.session.get(
                f"{BASE_URL}/api/org-chart",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    exists = data.get("exists", False)
                    self.log_test("API", "Org chart endpoint", True,
                                f"Chart exists: {exists}")
                else:
                    self.log_test("API", "Org chart endpoint", False, f"Status {resp.status}")
        except Exception as e:
            self.log_test("API", "Org chart endpoint", False, str(e))
            
        # Test documents list
        try:
            async with self.session.get(
                f"{BASE_URL}/api/documents",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    docs = await resp.json()
                    doc_count = len(docs.get("documents", []))
                    self.log_test("API", "Documents endpoint", True,
                                f"{doc_count} documents")
                else:
                    self.log_test("API", "Documents endpoint", False, f"Status {resp.status}")
        except Exception as e:
            self.log_test("API", "Documents endpoint", False, str(e))
            
    async def test_user_journey(self):
        """Test the complete user journey flow"""
        print(f"\n{BLUE}=== Testing User Journey Flow ==={RESET}")
        
        # Check if user needs onboarding
        if not self.user_data.get("onboarding_completed"):
            self.log_test("User Journey", "Onboarding needed", True, 
                        "User should be directed to onboarding")
        else:
            self.log_test("User Journey", "Onboarding completed", True,
                        "User can access main features")
            
        # Test file upload presigned URL
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/upload/presigned",
                    headers=headers,
                    json={
                        "filename": "test_document.pdf",
                        "content_type": "application/pdf"
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        has_url = bool(data.get("upload_url"))
                        self.log_test("User Journey", "File upload preparation", has_url,
                                    "Presigned URL generated" if has_url else "No URL returned")
                    else:
                        self.log_test("User Journey", "File upload preparation", False,
                                    f"Status {resp.status}")
            except Exception as e:
                self.log_test("User Journey", "File upload preparation", False, str(e))
                
    async def test_mobile_responsiveness(self):
        """Check if pages have mobile viewport meta tag"""
        print(f"\n{BLUE}=== Testing Mobile Responsiveness ==={RESET}")
        
        # Check dashboard for mobile meta tags
        try:
            async with self.session.get(f"{PLATFORM_URL}/web/dashboard-enhanced.html") as resp:
                if resp.status == 200:
                    content = await resp.text()
                    has_viewport = 'viewport' in content
                    has_responsive = 'responsive' in content or 'mobile' in content
                    self.log_test("Mobile", "Viewport meta tag", has_viewport,
                                "Mobile viewport configured" if has_viewport else "Missing viewport tag")
                    self.log_test("Mobile", "Responsive elements", has_responsive,
                                "Responsive design detected" if has_responsive else "May lack responsive design")
        except Exception as e:
            self.log_test("Mobile", "Mobile responsiveness check", False, str(e))
            
    def generate_report(self):
        """Generate summary report of all tests"""
        print(f"\n{BLUE}=== Test Summary Report ==={RESET}")
        print("=" * 60)
        
        # Group by category
        categories = {}
        for result in self.test_results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0, "tests": []}
            if result["passed"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
            categories[cat]["tests"].append(result)
            
        # Print category summaries
        total_passed = 0
        total_failed = 0
        
        for cat, data in categories.items():
            passed = data["passed"]
            failed = data["failed"]
            total = passed + failed
            total_passed += passed
            total_failed += failed
            
            print(f"\n{cat}:")
            print(f"  Passed: {passed}/{total} ({passed/total*100:.1f}%)")
            if failed > 0:
                print(f"  Failed tests:")
                for test in data["tests"]:
                    if not test["passed"]:
                        print(f"    - {test['test']}: {test['notes']}")
                        
        # Overall score
        total_tests = total_passed + total_failed
        score = (total_passed / total_tests * 10) if total_tests > 0 else 0
        
        print(f"\n{BLUE}Overall Results:{RESET}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
        print(f"Failed: {total_failed}")
        print(f"\n{BLUE}Customer Experience Score: {score:.1f}/10{RESET}")
        
        # Recommendations
        print(f"\n{BLUE}Recommendations:{RESET}")
        if total_failed == 0:
            print("✅ All systems functioning well!")
        else:
            if any(not r["passed"] for r in self.test_results if r["category"] == "Authentication"):
                print("🔧 Fix authentication issues - users cannot access the platform")
            if any(not r["passed"] for r in self.test_results if r["category"] == "Navigation"):
                print("🔧 Fix broken navigation links - users cannot access all features")
            if any(not r["passed"] for r in self.test_results if r["category"] == "API"):
                print("🔧 Fix API endpoints - features may not work properly")
            if any(not r["passed"] for r in self.test_results if r["category"] == "Data Persistence"):
                print("🔧 Fix data persistence - users lose their information")
                
async def main():
    """Run all tests"""
    print(f"{BLUE}MapMyStandards Platform - Complete User Experience Test{RESET}")
    print(f"Testing with user: {TEST_EMAIL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tester = UserExperienceTest()
    await tester.setup()
    
    try:
        # Run all test suites
        await tester.test_login()
        await tester.test_navigation_links()
        await tester.test_api_endpoints()
        await tester.test_user_journey()
        await tester.test_mobile_responsiveness()
        
        # Generate report
        tester.generate_report()
        
    finally:
        await tester.teardown()
        
if __name__ == "__main__":
    asyncio.run(main())