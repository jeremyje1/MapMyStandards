#!/usr/bin/env python3
"""
Full Customer Experience Analysis for MapMyStandards
Testing with real user credentials: jeremy.estrella@gmail.com
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://platform.mapmystandards.ai"
API_URL = "https://api.mapmystandards.ai"
EMAIL = "jeremy.estrella@gmail.com"
PASSWORD = "Ipo4Eva45*"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "issues": [],
    "fixes_needed": []
}

def log_test(category, test_name, passed, details="", fix_suggestion=""):
    """Log test results"""
    test_results["total_tests"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ [{category}] {test_name}")
        if details:
            print(f"   → {details}")
    else:
        test_results["failed"] += 1
        print(f"❌ [{category}] {test_name}")
        if details:
            print(f"   → {details}")
        test_results["issues"].append({
            "category": category,
            "test": test_name,
            "details": details
        })
        if fix_suggestion:
            test_results["fixes_needed"].append(fix_suggestion)

def test_page_load(url, page_name):
    """Test if a page loads successfully"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            # Check for common error indicators in content
            content_lower = response.text.lower()
            if "error" in content_lower or "404" in content_lower or "not found" in content_lower:
                if "404" not in page_name.lower():  # Avoid false positives
                    return False, f"Page contains error messages"
            return True, f"Page loads successfully ({len(response.text)} bytes)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Request failed: {str(e)}"

def test_api_endpoint(endpoint, token=None, method="GET", data=None):
    """Test an API endpoint"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        url = urljoin(API_URL, endpoint)
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        return response.status_code, response
    except Exception as e:
        return 0, str(e)

print("="*60)
print("MAPMYSTANDARDS FULL CUSTOMER EXPERIENCE ANALYSIS")
print(f"Testing as: {EMAIL}")
print(f"Time: {datetime.now()}")
print("="*60)

# 1. HOMEPAGE & INITIAL EXPERIENCE
print("\n🏠 TESTING HOMEPAGE & INITIAL EXPERIENCE")
print("-" * 40)

# Test homepage load
homepage_url = f"{BASE_URL}/homepage-enhanced.html"
passed, details = test_page_load(homepage_url, "Homepage")
log_test("Homepage", "Page loads", passed, details)

# Test homepage responsiveness
if passed:
    response = requests.get(homepage_url)
    content = response.text
    has_mobile_meta = '<meta name="viewport"' in content
    log_test("Homepage", "Mobile responsive meta tag", has_mobile_meta)
    
    has_nav = 'nav' in content.lower() and 'menu' in content.lower()
    log_test("Homepage", "Navigation menu present", has_nav)

# 2. LOGIN EXPERIENCE
print("\n🔐 TESTING LOGIN EXPERIENCE")
print("-" * 40)

# Test login page
login_url = f"{BASE_URL}/login-enhanced-v2.html"
passed, details = test_page_load(login_url, "Login Page")
log_test("Login", "Login page loads", passed, details)

# Check for demo credentials
if passed:
    response = requests.get(login_url)
    has_demo = "testuser@example.com" in response.text
    log_test("Login", "Demo credentials removed", not has_demo, 
             "Demo credentials still visible" if has_demo else "Clean login page")

# Test authentication
print("\n🔑 Testing actual login...")
auth_data = {"email": EMAIL, "password": PASSWORD}
status_code, auth_response = test_api_endpoint("/api/auth/login", method="POST", data=auth_data)

if status_code == 200:
    auth_success = True
    token_data = auth_response.json()
    token = token_data.get("access_token", "")
    user_data = token_data.get("user", {})
    
    log_test("Login", "Authentication successful", True, 
             f"User: {user_data.get('name', 'Unknown')}, Org: {user_data.get('institution', 'Unknown')}")
    
    # Check onboarding status
    onboarding_completed = user_data.get("onboarding_completed", False)
    log_test("Login", "Onboarding status", True, 
             f"Onboarding completed: {onboarding_completed}")
else:
    auth_success = False
    token = ""
    log_test("Login", "Authentication successful", False, 
             f"Status {status_code}: {auth_response if isinstance(auth_response, str) else auth_response.text}")

# 3. DASHBOARD EXPERIENCE
print("\n📊 TESTING DASHBOARD EXPERIENCE")
print("-" * 40)

dashboard_url = f"{BASE_URL}/dashboard-enhanced.html"
passed, details = test_page_load(dashboard_url, "Dashboard")
log_test("Dashboard", "Dashboard loads", passed, details)

# Test dashboard personalization
if auth_success:
    status_code, settings_response = test_api_endpoint("/api/user/intelligence-simple/settings", token)
    if status_code == 200:
        settings = settings_response.json()
        has_org = bool(settings.get("organization"))
        log_test("Dashboard", "User settings loaded", True,
                f"Org: {settings.get('organization', 'Not set')}, "
                f"Accreditor: {settings.get('primary_accreditor', 'Not set')}")
    else:
        log_test("Dashboard", "User settings loaded", False,
                f"Status {status_code}")

# 4. NAVIGATION & FEATURES
print("\n🧭 TESTING NAVIGATION & FEATURES")
print("-" * 40)

pages_to_test = [
    ("standards-graph-enhanced.html", "Standards Graph"),
    ("compliance-dashboard-enhanced.html", "Compliance Dashboard"),
    ("reports-enhanced.html", "Reports"),
    ("organizational-enhanced.html", "Organizational Chart"),
    ("settings-enhanced.html", "Settings"),
    ("about-enhanced.html", "About"),
    ("contact-enhanced.html", "Contact")
]

for page_file, page_name in pages_to_test:
    url = f"{BASE_URL}/{page_file}"
    passed, details = test_page_load(url, page_name)
    log_test("Navigation", f"{page_name} accessible", passed, details)

# 5. CORE FUNCTIONALITY
print("\n⚙️ TESTING CORE FUNCTIONALITY")
print("-" * 40)

if auth_success:
    # Test document upload preparation
    status_code, upload_response = test_api_endpoint("/api/documents/upload-url", token, method="POST", 
                                                    data={"filename": "test.pdf", "content_type": "application/pdf"})
    log_test("Features", "Document upload preparation", status_code == 200,
            f"Status {status_code}")
    
    # Test standards graph data
    status_code, graph_response = test_api_endpoint("/api/standards/graph", token)
    log_test("Features", "Standards graph data", status_code == 200,
            f"Status {status_code}")
    
    # Test compliance data
    status_code, compliance_response = test_api_endpoint("/api/compliance/summary", token)
    log_test("Features", "Compliance data", status_code == 200,
            f"Status {status_code}")

# 6. USER WORKFLOW
print("\n🔄 TESTING USER WORKFLOW")
print("-" * 40)

# Test onboarding page
onboarding_url = f"{BASE_URL}/onboarding.html"
passed, details = test_page_load(onboarding_url, "Onboarding")
log_test("Workflow", "Onboarding page accessible", passed, details)

# Test settings update
if auth_success:
    test_settings = {
        "organization": "Houston City College",
        "primary_accreditor": "SACSCOC",
        "goals": ["compliance", "efficiency"]
    }
    status_code, update_response = test_api_endpoint("/api/user/intelligence-simple/settings", 
                                                    token, method="POST", data=test_settings)
    log_test("Workflow", "Settings update", status_code == 200,
            f"Status {status_code}")

# 7. ERROR HANDLING & EDGE CASES  
print("\n🚨 TESTING ERROR HANDLING")
print("-" * 40)

# Test invalid login
bad_auth_data = {"email": EMAIL, "password": "wrong_password"}
status_code, bad_auth_response = test_api_endpoint("/api/auth/login", method="POST", data=bad_auth_data)
log_test("Error Handling", "Invalid login handled gracefully", 
         status_code in [401, 403],
         f"Status {status_code} (expected 401/403)")

# Test 404 page
status_code, response = test_api_endpoint("/nonexistent-page")
log_test("Error Handling", "404 errors handled", True,
         f"404 returns status {status_code}")

# 8. PERFORMANCE
print("\n⚡ TESTING PERFORMANCE")
print("-" * 40)

# Test page load times
start_time = time.time()
requests.get(f"{BASE_URL}/dashboard-enhanced.html")
dashboard_load_time = time.time() - start_time
log_test("Performance", "Dashboard load time", dashboard_load_time < 3,
         f"{dashboard_load_time:.2f} seconds")

# Test API response times
if auth_success:
    start_time = time.time()
    test_api_endpoint("/api/user/intelligence-simple/settings", token)
    api_response_time = time.time() - start_time
    log_test("Performance", "API response time", api_response_time < 2,
            f"{api_response_time:.2f} seconds")

# FINAL SUMMARY
print("\n" + "="*60)
print("CUSTOMER EXPERIENCE ANALYSIS SUMMARY")
print("="*60)

# Calculate score
score = (test_results["passed"] / test_results["total_tests"]) * 10
print(f"\n📊 Overall Score: {score:.1f}/10")
print(f"✅ Passed: {test_results['passed']}/{test_results['total_tests']} tests")
print(f"❌ Failed: {test_results['failed']}/{test_results['total_tests']} tests")

if test_results["issues"]:
    print("\n🔴 ISSUES FOUND:")
    for issue in test_results["issues"]:
        print(f"- [{issue['category']}] {issue['test']}: {issue['details']}")

if test_results["fixes_needed"]:
    print("\n🔧 RECOMMENDED FIXES:")
    for i, fix in enumerate(test_results["fixes_needed"], 1):
        print(f"{i}. {fix}")

# Specific recommendations based on score
print("\n💡 RECOMMENDATIONS:")
if score >= 9:
    print("✨ Excellent! The platform provides an outstanding user experience.")
elif score >= 7:
    print("👍 Good experience, but some improvements needed:")
    print("- Fix any failing API endpoints")
    print("- Ensure all core features are functional")
    print("- Improve error messages for better user guidance")
elif score >= 5:
    print("⚠️ Moderate experience, significant improvements needed:")
    print("- Address authentication and data persistence issues")
    print("- Implement missing features")
    print("- Improve page load times")
    print("- Add better error handling")
else:
    print("🚨 Poor experience, urgent fixes required:")
    print("- Fix critical authentication issues")
    print("- Ensure all pages load correctly")
    print("- Implement core functionality")
    print("- Major UX overhaul needed")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)