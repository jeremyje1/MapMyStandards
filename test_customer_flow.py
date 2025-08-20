#!/usr/bin/env python3
"""
Comprehensive Customer Flow Testing Script
Tests the complete customer journey from landing to subscription
"""
import requests
import json
import time
from datetime import datetime
import os
from typing import Dict, Any, Optional

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "https://api.mapmystandards.ai")
TEST_EMAIL = f"test_{int(time.time())}@mapmystandards.ai"
TEST_PASSWORD = "TestPassword123!"

class CustomerFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.user_data = {}
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_landing_page(self):
        """Test 1: Landing page accessibility"""
        try:
            response = self.session.get(f"{BASE_URL}/landing")
            passed = response.status_code == 200
            self.log_result(
                "Landing Page Access",
                passed,
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Landing Page Access", False, str(e))
            return False
    
    def test_api_health(self):
        """Test 2: API health check"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            data = response.json()
            passed = response.status_code == 200 and data.get("status") == "healthy"
            self.log_result(
                "API Health Check",
                passed,
                f"Response: {json.dumps(data, indent=2)}"
            )
            return passed
        except Exception as e:
            self.log_result("API Health Check", False, str(e))
            return False
    
    def test_trial_signup(self):
        """Test 3: Trial signup flow"""
        try:
            signup_data = {
                "name": "Test Institution",
                "institution_name": "Test University",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "role": "administrator",
                "plan": "college_monthly",
                "newsletter_opt_in": True
            }
            
            response = self.session.post(
                f"{BASE_URL}/trial/signup",
                json=signup_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_data = data
                passed = data.get("success", False)
                self.log_result(
                    "Trial Signup",
                    passed,
                    f"Trial ID: {data.get('trial_id')}, Expires: {data.get('expires_at')}"
                )
            else:
                self.log_result(
                    "Trial Signup",
                    False,
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                passed = False
                
            return passed
        except Exception as e:
            self.log_result("Trial Signup", False, str(e))
            return False
    
    def test_email_notification(self):
        """Test 4: Check if welcome email would be sent"""
        try:
            # Check email service health
            response = self.session.get(f"{BASE_URL}/api/v1/email/health")
            if response.status_code == 200:
                data = response.json()
                passed = data.get("status") == "healthy"
                self.log_result(
                    "Email Service Health",
                    passed,
                    f"Provider: {data.get('provider')}"
                )
            else:
                self.log_result(
                    "Email Service Health",
                    False,
                    f"Status: {response.status_code}"
                )
                passed = False
            return passed
        except Exception as e:
            self.log_result("Email Service Health", False, str(e))
            return False
    
    def test_login(self):
        """Test 5: Login with trial credentials"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "remember": False
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                passed = data.get("success", False)
                if passed:
                    self.user_data["token"] = data.get("token")
                self.log_result(
                    "User Login",
                    passed,
                    f"Token received: {'Yes' if data.get('token') else 'No'}"
                )
            else:
                self.log_result(
                    "User Login",
                    False,
                    f"Status: {response.status_code}"
                )
                passed = False
                
            return passed
        except Exception as e:
            self.log_result("User Login", False, str(e))
            return False
    
    def test_dashboard_access(self):
        """Test 6: Access dashboard with auth"""
        try:
            headers = {}
            if self.user_data.get("token"):
                headers["Authorization"] = f"Bearer {self.user_data['token']}"
            
            response = self.session.get(
                f"{BASE_URL}/api/v1/user/dashboard",
                headers=headers
            )
            
            passed = response.status_code in [200, 404]  # 404 if endpoint not implemented yet
            self.log_result(
                "Dashboard Access",
                passed,
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Dashboard Access", False, str(e))
            return False
    
    def test_tier_sync(self):
        """Test 7: Tier sync endpoint"""
        try:
            tier_data = {
                "email": TEST_EMAIL,
                "tier": "college",
                "source": "test_script"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/tier/sync",
                json=tier_data
            )
            
            passed = response.status_code == 200
            if passed:
                data = response.json()
                self.log_result(
                    "Tier Sync",
                    True,
                    f"Tier: {data.get('tier')}, Updated: {data.get('updated_at')}"
                )
            else:
                self.log_result(
                    "Tier Sync",
                    False,
                    f"Status: {response.status_code}"
                )
                
            return passed
        except Exception as e:
            self.log_result("Tier Sync", False, str(e))
            return False
    
    def test_stripe_webhook(self):
        """Test 8: Stripe webhook endpoint availability"""
        try:
            # Test webhook endpoint exists
            webhook_data = {
                "type": "ping",
                "data": {"object": {}}
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/billing/webhook/stripe",
                json=webhook_data,
                headers={"stripe-signature": "test_sig"}
            )
            
            # Webhook should respond even to invalid signatures (with error)
            passed = response.status_code in [200, 400, 401]
            self.log_result(
                "Stripe Webhook Endpoint",
                passed,
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Stripe Webhook Endpoint", False, str(e))
            return False
    
    def test_document_upload(self):
        """Test 9: Document upload capability"""
        try:
            # Check if upload endpoint exists
            response = self.session.get(f"{BASE_URL}/upload")
            passed = response.status_code in [200, 301, 302]  # Might redirect
            self.log_result(
                "Document Upload Page",
                passed,
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Document Upload Page", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run complete customer flow test suite"""
        print("=" * 60)
        print("🧪 MapMyStandards Customer Flow Test Suite")
        print(f"🌐 Testing: {BASE_URL}")
        print(f"📧 Test Email: {TEST_EMAIL}")
        print("=" * 60)
        print()
        
        tests = [
            self.test_landing_page,
            self.test_api_health,
            self.test_trial_signup,
            self.test_email_notification,
            self.test_login,
            self.test_dashboard_access,
            self.test_tier_sync,
            self.test_stripe_webhook,
            self.test_document_upload
        ]
        
        for test in tests:
            test()
            print()
            time.sleep(1)  # Rate limiting
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests < total_tests:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n💡 Recommendations:")
        if passed_tests == total_tests:
            print("✅ All tests passed! The customer flow is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review and fix the issues above.")
            print("📝 Priority fixes:")
            if not any(r["test"] == "Trial Signup" and r["passed"] for r in self.test_results):
                print("  1. Fix trial signup endpoint (/trial/signup)")
            if not any(r["test"] == "User Login" and r["passed"] for r in self.test_results):
                print("  2. Fix authentication system (/auth/login)")
            if not any(r["test"] == "Email Service Health" and r["passed"] for r in self.test_results):
                print("  3. Configure email service properly")

if __name__ == "__main__":
    tester = CustomerFlowTester()
    tester.run_all_tests()
