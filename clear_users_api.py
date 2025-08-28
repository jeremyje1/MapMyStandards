#!/usr/bin/env python3
"""
Clear test users via API endpoint
"""

import requests
import json

def clear_users():
    """Clear users via API"""
    base_url = "https://platform.mapmystandards.ai"
    
    try:
        # First check health to make sure API is available
        print("🔍 Checking API health...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code != 200:
            print(f"❌ API not healthy: {health_response.status_code}")
            return
        
        print("✅ API is healthy")
        
        # Confirm deletion
        print("\n⚠️ WARNING: This will delete ALL users from the production database!")
        confirm = input("Type 'DELETE ALL USERS' to confirm: ")
        
        if confirm != "DELETE ALL USERS":
            print("❌ Operation cancelled")
            return
        
        print("🗑️ Clearing all users...")
        
        # Call the admin endpoint to clear users
        clear_response = requests.post(
            f"{base_url}/admin/clear-users",
            params={"confirm": "DELETE_ALL_USERS"},
            timeout=30
        )
        
        if clear_response.status_code == 200:
            result = clear_response.json()
            if result.get("success"):
                print(f"✅ {result['message']}")
                print(f"⚠️ {result['warning']}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ API error: {clear_response.status_code} - {clear_response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🗑️ User Cleanup Tool")
    print("=" * 30)
    clear_users()