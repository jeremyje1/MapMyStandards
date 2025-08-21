#!/usr/bin/env python3
"""Monitor Railway deployment status"""

import requests
import time
import json

API_URL = "https://api.mapmystandards.ai"
FRONTEND_URL = "https://platform.mapmystandards.ai"

print("🔄 Monitoring Railway Deployment...")
print("=" * 50)
print(f"API: {API_URL}")
print(f"Frontend: {FRONTEND_URL}")
print("\nWaiting for deployment to complete...")

start_time = time.time()
max_wait = 300  # 5 minutes
last_status = None

while time.time() - start_time < max_wait:
    try:
        # Check health endpoint
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            
            if status != last_status:
                print(f"\n✅ API responding! Status: {status}")
                print(f"   Version: {data.get('version', 'unknown')}")
                print(f"   Environment: {data.get('environment', 'unknown')}")
                
                # Check services
                services = data.get("services", {})
                if services:
                    print("   Services:")
                    for service, info in services.items():
                        print(f"     - {service}: {info.get('status', 'unknown')}")
                
                last_status = status
                
                # If API is healthy, test signup
                if status in ["healthy", "degraded"]:
                    print("\n📝 Testing trial signup...")
                    test_email = f"deploy_test_{int(time.time())}@example.com"
                    signup_data = {
                        "name": "Deploy Test",
                        "institution_name": "Test Org",
                        "email": test_email,
                        "password": "Test123!",
                        "role": "Administrator"
                    }
                    
                    signup_resp = requests.post(
                        f"{API_URL}/api/trial/signup",
                        json=signup_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if signup_resp.status_code == 200:
                        print("   ✅ Trial signup working!")
                        print("   🎉 Deployment successful!")
                        break
                    elif signup_resp.status_code == 500:
                        print("   ⚠️ Signup returning 500 - check logs")
                    else:
                        print(f"   ❌ Signup returned {signup_resp.status_code}")
            else:
                print(".", end="", flush=True)
                
        else:
            print(".", end="", flush=True)
            
    except requests.exceptions.RequestException:
        print(".", end="", flush=True)
    
    time.sleep(5)

elapsed = int(time.time() - start_time)
print(f"\n\nTotal monitoring time: {elapsed} seconds")

if elapsed >= max_wait:
    print("⏱️ Monitoring timeout reached")
    print("Check Railway dashboard for deployment status")
else:
    print("\n✅ Deployment complete!")
    print(f"API docs: {API_URL}/docs")
    print(f"Frontend: {FRONTEND_URL}")
