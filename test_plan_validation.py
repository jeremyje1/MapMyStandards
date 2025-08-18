#!/usr/bin/env python3
"""
Test script for production API - checking plan validation
"""
import requests
import json
from datetime import datetime
import random

# Use current timestamp to ensure unique emails/usernames
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
random_suffix = random.randint(1000, 9999)

# Production API URL  
BASE_URL = "https://api.mapmystandards.ai"

def test_plan_validation():
    """Test different plan values to see what's accepted"""
    
    # Test data
    base_data = {
        "firstName": "Test",
        "lastName": "User", 
        "email": f"test+{timestamp}_{random_suffix}@mapmystandards.ai",
        "institution": "Test Organization",
        "username": f"testuser{random_suffix}",
        "password": "password123"
    }
    
    # Test different plan values
    plans_to_test = ["monthly", "annual", "Monthly", "Annual", "MONTHLY", "ANNUAL"]
    
    print("🧪 Plan Validation Test")
    print("=" * 60)
    
    for plan in plans_to_test:
        print(f"\n🔍 Testing plan: '{plan}'")
        
        test_data = base_data.copy()
        test_data["plan"] = plan
        test_data["email"] = f"test+{timestamp}_{random_suffix}_{plan}@mapmystandards.ai"
        test_data["username"] = f"testuser{random_suffix}_{plan}"
        
        try:
            response = requests.post(
                f"{BASE_URL}/create-trial-account",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS")
                result = response.json()
                if "checkout_url" in result:
                    print(f"🔗 Checkout URL: {result['checkout_url'][:80]}...")
            else:
                print("❌ FAILED")
                try:
                    error = response.json()
                    print(f"📝 Error: {error}")
                except:
                    print(f"📝 Raw response: {response.text}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_plan_validation()
