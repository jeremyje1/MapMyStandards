#!/usr/bin/env python3
"""Check if the deployment is complete"""

import requests
import time

print("Checking deployment progress...")
print("=" * 60)

# Check the API health endpoint
API_BASE = "https://api.mapmystandards.ai"

for i in range(10):  # Check for up to 2 minutes
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print(f"\n✅ API is responding (attempt {i+1})")
            
            # Check if our changes are deployed by looking at the JWT debug endpoint
            response = requests.get(f"{API_BASE}/api/debug/jwt-config")
            if response.status_code == 200:
                config = response.json()
                model_id = config.get("bedrock_model_id", "")
                if "20240620-v1:0" in model_id:
                    print("\n✅ NEW CODE IS DEPLOYED!")
                    print(f"   Bedrock Model ID: {model_id}")
                    print("\n🎉 Deployment successful! The analyze/download features should work now.")
                    break
                else:
                    print(f"\n⏳ Deployment in progress... (old model ID: {model_id})")
            else:
                print("\n⏳ Deployment in progress...")
        else:
            print(f"\n⏳ API returned {response.status_code}, deployment may be in progress...")
    except Exception as e:
        print(f"\n⏳ API not responding yet (attempt {i+1})... {str(e)[:50]}")
    
    if i < 9:
        print("   Waiting 15 seconds before next check...")
        time.sleep(15)

print("\n" + "=" * 60)
print("Note: Railway deployments typically take 2-5 minutes.")
print("You can also check: https://railway.app/dashboard")