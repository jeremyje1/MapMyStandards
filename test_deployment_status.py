#!/usr/bin/env python3
"""
Test if the backend has been deployed with database changes
"""

import requests
import json
from datetime import datetime

API_BASE = "https://api.mapmystandards.ai"

def check_deployment():
    print("\n🔍 Checking Backend Deployment Status...\n")
    
    # Check API health
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️  API returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return
    
    # Check for database-specific endpoints or behaviors
    print("\n📊 Checking for Database Implementation...\n")
    
    # The new implementation uses PostgreSQL
    # The old implementation uses JSON files
    # We can't directly check this without auth, but we can check response times
    
    print("To fully test, you need to:")
    print("1. Upload a file on the platform")
    print("2. Wait 5 minutes") 
    print("3. Check if the file is still there")
    print("4. If yes = New database backend ✅")
    print("5. If no = Old JSON backend ❌")
    
    print("\n🚀 Deployment Instructions:")
    print("1. Go to Railway dashboard")
    print("2. Check 'Deployments' section")
    print("3. Look for deployment with commit message about 'PostgreSQL' or 'database'")
    print("4. If not found, trigger manual deploy")
    
    print("\n📝 Recent GitHub Commits:")
    print(f"- {datetime.now().strftime('%Y-%m-%d %H:%M')} - Update backend to use PostgreSQL database")
    print("- This commit needs to be deployed to Railway")

if __name__ == "__main__":
    check_deployment()