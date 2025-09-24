#!/usr/bin/env python3
"""Check if the new documents API is deployed and working."""

import requests
import time
import sys

def check_documents_api():
    """Check the status of the documents API deployment."""
    print("\n=== Checking Documents API Deployment ===")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # First check if API is up
    print("1. Checking API health...")
    try:
        health_response = requests.get("https://api.mapmystandards.ai/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️  API returned status {health_response.status_code}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False
    
    # Login to get token
    print("\n2. Getting auth token...")
    try:
        auth_response = requests.post(
            "https://api.mapmystandards.ai/api/auth/login",
            json={
                "email": "jeremy@mapmystandards.com",
                "password": "Test123!@#"
            },
            timeout=10
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check documents endpoint
    print("\n3. Checking documents endpoint...")
    try:
        docs_response = requests.get(
            "https://api.mapmystandards.ai/api/documents",
            headers=headers,
            timeout=10
        )
        
        if docs_response.status_code == 200:
            print("✅ Documents endpoint is working!")
            data = docs_response.json()
            print(f"   Found {len(data.get('documents', []))} documents")
            return True
        elif docs_response.status_code == 404:
            print("⏳ Documents endpoint not found - deployment may still be in progress")
            print("   This is normal if Railway is still building")
            return False
        else:
            print(f"⚠️  Documents endpoint returned {docs_response.status_code}")
            print(f"   Response: {docs_response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Documents check failed: {e}")
        return False

def main():
    """Monitor deployment status."""
    max_checks = 20  # Check for up to 5 minutes
    check_interval = 15  # seconds
    
    print("Monitoring Railway deployment...")
    print("This typically takes 2-3 minutes")
    print("-" * 50)
    
    for i in range(max_checks):
        if check_documents_api():
            print("\n" + "=" * 50)
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("=" * 50)
            print("\nThe enhanced upload functionality is now live!")
            print("\nYou can now:")
            print("1. Go to https://platform.mapmystandards.ai/dashboard-enhanced")
            print("2. Click 'Upload Documents'")
            print("3. Upload files with S3 integration!")
            sys.exit(0)
        
        if i < max_checks - 1:
            print(f"\nWaiting {check_interval} seconds before next check...")
            print(f"Check {i+1}/{max_checks}")
            time.sleep(check_interval)
    
    print("\n" + "=" * 50)
    print("⚠️  TIMEOUT - Deployment may still be in progress")
    print("=" * 50)
    print("\nCheck Railway dashboard at:")
    print("https://railway.app/project/prolific-fulfillment")
    sys.exit(1)

if __name__ == "__main__":
    main()
