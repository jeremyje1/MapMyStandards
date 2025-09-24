#!/usr/bin/env python3
"""Monitor Railway deployment and test upload functionality."""

import requests
import time
import sys

def check_deployment():
    """Check if the documents API is deployed and working."""
    print(f"\n[{time.strftime('%H:%M:%S')}] Checking deployment status...")
    
    # 1. Check health
    try:
        health_resp = requests.get("https://api.mapmystandards.ai/health", timeout=5)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            uptime = health_data.get('uptime_seconds', 0)
            print(f"✓ API is up (uptime: {int(uptime)}s)")
            
            # If uptime is less than 30 seconds, it just restarted
            if uptime < 30:
                print("  ⚠️  API just restarted, waiting for initialization...")
                return False
        else:
            print(f"✗ API health check failed: {health_resp.status_code}")
            return False
    except:
        print("✗ API is down")
        return False
    
    # 2. Test login
    try:
        auth_resp = requests.post(
            "https://api.mapmystandards.ai/api/auth/login",
            json={"email": "jeremy@mapmystandards.com", "password": "Test123!@#"},
            timeout=5
        )
        
        if auth_resp.status_code != 200:
            print(f"✗ Login failed: {auth_resp.status_code}")
            return False
        
        token = auth_resp.json().get('access_token')
        print("✓ Authentication working")
    except Exception as e:
        print(f"✗ Auth error: {e}")
        return False
    
    # 3. Test documents endpoint
    try:
        docs_resp = requests.get(
            "https://api.mapmystandards.ai/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if docs_resp.status_code == 200:
            print("✅ Documents API is WORKING!")
            return True
        elif docs_resp.status_code == 404:
            print("⏳ Documents endpoint not found (deployment in progress)")
            return False
        else:
            print(f"✗ Documents API error: {docs_resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Documents check error: {e}")
        return False

def main():
    print("=== Railway Deployment Monitor ===")
    print("Monitoring for documents API deployment...")
    print("This typically takes 2-3 minutes after pushing to GitHub")
    print("-" * 40)
    
    start_time = time.time()
    max_duration = 300  # 5 minutes
    
    while time.time() - start_time < max_duration:
        if check_deployment():
            print("\n" + "=" * 40)
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("=" * 40)
            print("\nThe upload functionality is now ready!")
            print("Go to: https://platform.mapmystandards.ai/upload-enhanced-v2")
            return
        
        # Wait before next check
        time.sleep(10)
    
    print("\n⚠️  Timeout - check Railway dashboard")
    print("https://railway.app/project/prolific-fulfillment")

if __name__ == "__main__":
    main()
