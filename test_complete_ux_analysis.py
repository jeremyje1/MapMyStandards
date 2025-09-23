#!/usr/bin/env python3
"""
Complete UX Analysis for MapMyStandards Platform
Tests all user flows and provides detailed feedback
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "https://platform.mapmystandards.ai"
API_URL = "https://api.mapmystandards.ai/api"
TEST_USER = {
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def test_page_access(page_name, url, session=None):
    """Test if a page is accessible and returns expected status"""
    try:
        if session:
            response = session.get(url)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            # Check for common error patterns in the HTML
            content = response.text.lower()
            if 'error' in response.text and 'catch' not in response.text:
                return False, f"Page contains error messages"
            return True, f"Page loads successfully ({len(response.text)} bytes)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_api_endpoint(endpoint_name, url, method='GET', data=None, headers=None):
    """Test API endpoint functionality"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            return True, f"API responds correctly"
        elif response.status_code == 401:
            return False, f"Authentication required"
        elif response.status_code == 404:
            return False, f"Endpoint not found"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_authentication():
    """Test the complete authentication flow"""
    session = requests.Session()
    
    # Test login
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = session.post(f"{API_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                return True, f"Authentication successful", token, session
            else:
                return False, "No token received", None, session
        else:
            return False, f"Login failed: HTTP {response.status_code}", None, session
    except Exception as e:
        return False, f"Login error: {str(e)}", None, session

def run_complete_analysis():
    """Run complete UX analysis and provide scoring"""
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}COMPLETE UX ANALYSIS - MAPMYSTANDARDS{Colors.ENDC}")
    print(f"Testing as: {TEST_USER['email']}")
    print(f"Time: {datetime.now()}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    total_tests = 0
    passed_tests = 0
    critical_failures = []
    minor_issues = []
    
    # 1. PUBLIC PAGES TEST
    print(f"{Colors.BLUE}1. TESTING PUBLIC ACCESS{Colors.ENDC}")
    public_pages = [
        ("Homepage", f"{BASE_URL}/"),
        ("Login Page", f"{BASE_URL}/login-enhanced-v2.html"),
        ("About Page", f"{BASE_URL}/about-enhanced.html"),
        ("Contact Page", f"{BASE_URL}/contact-enhanced.html")
    ]
    
    for page_name, url in public_pages:
        total_tests += 1
        success, message = test_page_access(page_name, url)
        if success:
            print(f"  ✅ {page_name}: {message}")
            passed_tests += 1
        else:
            print(f"  ❌ {page_name}: {message}")
            minor_issues.append(f"{page_name}: {message}")
    
    # 2. AUTHENTICATION TEST
    print(f"\n{Colors.BLUE}2. TESTING AUTHENTICATION{Colors.ENDC}")
    total_tests += 1
    auth_success, auth_message, token, session = test_authentication()
    if auth_success:
        print(f"  ✅ Login: {auth_message}")
        passed_tests += 1
    else:
        print(f"  ❌ Login: {auth_message}")
        critical_failures.append(f"Authentication: {auth_message}")
        token = None
    
    # 3. PROTECTED PAGES TEST
    print(f"\n{Colors.BLUE}3. TESTING PROTECTED PAGES{Colors.ENDC}")
    protected_pages = [
        ("Dashboard", f"{BASE_URL}/dashboard-enhanced.html"),
        ("Upload Documents", f"{BASE_URL}/upload-enhanced.html"),
        ("Standards Graph", f"{BASE_URL}/standards-graph-enhanced.html"),
        ("Compliance Dashboard", f"{BASE_URL}/compliance-dashboard-enhanced.html"),
        ("Reports", f"{BASE_URL}/reports-enhanced.html"),
        ("Organizational Chart", f"{BASE_URL}/organizational-enhanced.html"),
        ("Settings", f"{BASE_URL}/settings-enhanced.html")
    ]
    
    for page_name, url in protected_pages:
        total_tests += 1
        success, message = test_page_access(page_name, url, session)
        if success:
            print(f"  ✅ {page_name}: {message}")
            passed_tests += 1
        else:
            print(f"  ❌ {page_name}: {message}")
            if page_name in ["Dashboard", "Upload Documents"]:
                critical_failures.append(f"{page_name}: {message}")
            else:
                minor_issues.append(f"{page_name}: {message}")
    
    # 4. API ENDPOINTS TEST
    print(f"\n{Colors.BLUE}4. TESTING API ENDPOINTS{Colors.ENDC}")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    api_endpoints = [
        ("User Profile", f"{API_URL}/users/me", "GET"),
        ("User Settings", f"{API_URL}/users/settings", "GET"),
        ("Documents List", f"{API_URL}/documents", "GET"),
        ("Standards Data", f"{API_URL}/standards/graph", "GET"),
        ("Upload Endpoint", f"{API_URL}/documents/upload", "POST")
    ]
    
    for endpoint_name, url, method in api_endpoints:
        total_tests += 1
        success, message = test_api_endpoint(endpoint_name, url, method, headers=headers)
        if success:
            print(f"  ✅ {endpoint_name}: {message}")
            passed_tests += 1
        else:
            print(f"  ❌ {endpoint_name}: {message}")
            if endpoint_name in ["User Profile", "Upload Endpoint"]:
                critical_failures.append(f"{endpoint_name} API: {message}")
            else:
                minor_issues.append(f"{endpoint_name} API: {message}")
    
    # 5. PERFORMANCE TEST
    print(f"\n{Colors.BLUE}5. TESTING PERFORMANCE{Colors.ENDC}")
    perf_pages = [
        ("Dashboard", f"{BASE_URL}/dashboard-enhanced.html"),
        ("Login", f"{BASE_URL}/login-enhanced-v2.html")
    ]
    
    for page_name, url in perf_pages:
        total_tests += 1
        start_time = time.time()
        response = requests.get(url)
        load_time = time.time() - start_time
        
        if load_time < 1.0:
            print(f"  ✅ {page_name} load time: {load_time:.2f}s")
            passed_tests += 1
        else:
            print(f"  ❌ {page_name} load time: {load_time:.2f}s (slow)")
            minor_issues.append(f"{page_name} performance: {load_time:.2f}s")
    
    # CALCULATE SCORE
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}ANALYSIS RESULTS{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    success_rate = (passed_tests / total_tests) * 100
    base_score = passed_tests / total_tests * 10
    
    # Apply penalties
    critical_penalty = len(critical_failures) * 1.5
    minor_penalty = len(minor_issues) * 0.3
    final_score = max(0, base_score - critical_penalty - minor_penalty)
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
    print(f"🎯 Base Score: {base_score:.1f}/10")
    print(f"⚠️  Critical Issues: {len(critical_failures)} (-{critical_penalty:.1f} points)")
    print(f"📝 Minor Issues: {len(minor_issues)} (-{minor_penalty:.1f} points)")
    print(f"\n{Colors.BOLD}🏆 FINAL UX SCORE: {final_score:.1f}/10{Colors.ENDC}")
    
    # DETAILED FEEDBACK
    if critical_failures:
        print(f"\n{Colors.RED}❌ CRITICAL FAILURES:{Colors.ENDC}")
        for issue in critical_failures:
            print(f"  • {issue}")
    
    if minor_issues:
        print(f"\n{Colors.YELLOW}⚠️  MINOR ISSUES:{Colors.ENDC}")
        for issue in minor_issues:
            print(f"  • {issue}")
    
    # RECOMMENDATIONS
    print(f"\n{Colors.BLUE}💡 RECOMMENDATIONS:{Colors.ENDC}")
    if final_score < 5:
        print("  • Fix authentication system immediately")
        print("  • Ensure all core pages are accessible")
        print("  • Implement missing API endpoints")
    elif final_score < 7:
        print("  • Complete API endpoint implementation")
        print("  • Add better error handling")
        print("  • Improve loading states")
    elif final_score < 9:
        print("  • Polish user interactions")
        print("  • Add progress indicators")
        print("  • Optimize performance")
    else:
        print("  • Platform is performing excellently!")
        print("  • Consider adding advanced features")
    
    # USER JOURNEY ASSESSMENT
    print(f"\n{Colors.BLUE}🚶 USER JOURNEY ASSESSMENT:{Colors.ENDC}")
    journey_score = 10
    journey_issues = []
    
    if not auth_success:
        journey_score -= 5
        journey_issues.append("Cannot log in")
    
    if "Dashboard" in [f.split(":")[0] for f in critical_failures]:
        journey_score -= 3
        journey_issues.append("Cannot access dashboard")
    
    if "Upload" in [f.split(":")[0] for f in critical_failures]:
        journey_score -= 2
        journey_issues.append("Cannot upload documents")
    
    print(f"  Journey Score: {journey_score}/10")
    if journey_issues:
        print("  Issues preventing smooth journey:")
        for issue in journey_issues:
            print(f"    - {issue}")
    else:
        print("  ✅ User can complete core journey successfully!")
    
    return final_score

if __name__ == "__main__":
    score = run_complete_analysis()
    
    if score >= 9:
        print(f"\n{Colors.GREEN}🎉 EXCELLENT! Platform exceeds expectations!{Colors.ENDC}")
    elif score >= 7:
        print(f"\n{Colors.YELLOW}👍 GOOD! Platform is functional but needs polish.{Colors.ENDC}")
    elif score >= 5:
        print(f"\n{Colors.YELLOW}⚠️  ACCEPTABLE. Platform has significant issues.{Colors.ENDC}")
    else:
        print(f"\n{Colors.RED}❌ POOR. Platform needs immediate attention.{Colors.ENDC}")