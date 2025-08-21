#!/usr/bin/env python3
"""Test the API after database fixes"""

import requests
import time
import json

API_URL = "https://api.mapmystandards.ai"

print("🧪 Testing API After Database Fixes")
print("=" * 50)

# First check the health endpoint
print("\n1️⃣ Checking API Health...")
health_response = requests.get(f"{API_URL}/health")
print(f"Status: {health_response.status_code}")

if health_response.status_code == 200:
    health_data = health_response.json()
    print(f"API Status: {health_data.get('status', 'unknown')}")
    
    # Check if it's our debug endpoint
    if "error" in health_data:
        print(f"❌ App failed to load: {health_data['error']}")
        print("\nChecking debug endpoint...")
        debug_response = requests.get(f"{API_URL}/debug/env")
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print("Environment status:")
            for key, value in debug_data.items():
                print(f"  {key}: {value}")
    else:
        print("✅ API is running!")
        print(f"Version: {health_data.get('version', 'unknown')}")
        
        # Try signup again
        print("\n2️⃣ Testing Trial Signup...")
        test_email = f"test_fixed_{int(time.time())}@example.com"
        
        signup_data = {
            "name": "Test User",
            "institution_name": "Test University",
            "email": test_email,
            "password": "TestPassword123!",
            "role": "Administrator",
            "plan": "professional"
        }
        
        signup_response = requests.post(
            f"{API_URL}/api/trial/signup",
            json=signup_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Signup status: {signup_response.status_code}")
        
        if signup_response.status_code == 200:
            print("✅ Trial signup working!")
            data = signup_response.json()
            print(f"User created: {data.get('user_id')}")
            print(f"Trial ends: {data.get('trial_end_date')}")
            
            # Test login
            if data.get("access_token"):
                print("\n3️⃣ Testing authenticated endpoints...")
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                
                dashboard = requests.get(f"{API_URL}/api/dashboard/overview", headers=headers)
                print(f"Dashboard access: {dashboard.status_code}")
                
                if dashboard.status_code == 200:
                    print("✅ Full authentication flow working!")
        else:
            print(f"❌ Signup still failing: {signup_response.text[:200]}")
            
            if signup_response.status_code == 500:
                print("\nPossible remaining issues:")
                print("1. DATABASE_URL format incorrect")
                print("2. Database not yet provisioned")
                print("3. Missing Stripe configuration")

else:
    print(f"❌ API not responding properly")
    print(f"Response: {health_response.text[:200]}")

print("\n" + "=" * 50)
print("Deployment status check complete!")
print(f"API URL: {API_URL}")
print("\nIf still having issues:")
print("1. Check Railway logs for detailed errors")
print("2. Ensure PostgreSQL database is added to the project")
print("3. Verify all environment variables are set correctly")
