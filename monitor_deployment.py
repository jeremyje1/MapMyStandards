#!/usr/bin/env python3
"""Monitor Railway deployment until the API is ready"""

import requests
import time
import sys

BASE_URL = "https://mapmystandards-prod-production.up.railway.app"

print("🔄 Monitoring Railway deployment...")
print(f"URL: {BASE_URL}")
print("Waiting for API to be ready...\n")

start_time = time.time()
max_wait = 300  # 5 minutes

while time.time() - start_time < max_wait:
    try:
        # Check if docs are available (indicates FastAPI is running)
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        
        if response.status_code == 200:
            print("\n✅ FastAPI is running! Checking endpoints...")
            
            # Test key endpoints
            endpoints = [
                ("/docs", "FastAPI Docs"),
                ("/health", "Health Check"),
                ("/api/trial/signup", "Trial Signup (expecting 405 for GET)"),
            ]
            
            for endpoint, name in endpoints:
                r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                print(f"   {name}: {r.status_code}")
            
            print("\n🎉 Deployment successful! API is ready.")
            print(f"   Documentation: {BASE_URL}/docs")
            print(f"   Total wait time: {int(time.time() - start_time)} seconds")
            sys.exit(0)
            
        else:
            # Still deploying
            elapsed = int(time.time() - start_time)
            print(f"\r⏳ Waiting... ({elapsed}s) - Status: {response.status_code}", end="", flush=True)
            
    except requests.exceptions.RequestException:
        elapsed = int(time.time() - start_time)
        print(f"\r⏳ Waiting... ({elapsed}s) - Connection failed", end="", flush=True)
    
    time.sleep(5)

print("\n\n❌ Timeout waiting for deployment. Check Railway logs.")
sys.exit(1)
