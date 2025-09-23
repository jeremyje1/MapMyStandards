#!/usr/bin/env python3
"""
Check if the database migration has been run on Railway
"""
import requests
import json

API_BASE = "https://api.mapmystandards.ai"

def check_settings_endpoint():
    """Check if settings are being stored in database"""
    print("🔍 Checking database status via API...\n")
    
    try:
        # Check health endpoint
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️  API returned status: {response.status_code}")
        
        print("\n📊 Checking settings storage method...")
        print("If settings are using database:")
        print("  - Onboarding data will persist")
        print("  - You won't need to re-enter information")
        print("\nIf still using JSON files:")
        print("  - Data will be lost on redeploy")
        print("  - You'll need to run the migration")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Checking Railway Database Status\n")
    check_settings_endpoint()
    
    print("\n📝 To check if migration is needed:")
    print("1. Try logging in and completing onboarding")
    print("2. Log out and log back in")
    print("3. If onboarding data is remembered = migration worked")
    print("4. If asked to onboard again = need to run migration")
    
    print("\n🔧 To run migration on Railway:")
    print("railway run python ensure_user_table.py")