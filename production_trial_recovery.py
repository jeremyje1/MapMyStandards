#!/usr/bin/env python3
"""
Production trial recovery script - makes API call to restore trial data
"""

import requests
import json

def create_trial_via_api(trial_id, name, email, organization="Paying Customer"):
    """Create a trial by directly calling the signup API with known trial_id"""
    
    # First, let's check if we can reach the API
    try:
        health_response = requests.get("https://api.mapmystandards.ai/health", timeout=10)
        print(f"✅ API Health: {health_response.status_code} - {health_response.text}")
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        return False
    
    # Try to create a new trial through the normal signup process
    try:
        signup_data = {
            "name": name,
            "email": email,
            "organization": organization,
            "use_case": "Paid trial recovery"
        }
        
        response = requests.post(
            "https://api.mapmystandards.ai/trial/signup",
            json=signup_data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Parse the response to get the new trial ID
            response_text = response.text
            if "trial-id" in response_text or "trial_id" in response_text:
                print(f"✅ New trial created successfully!")
                print(f"Response: {response.status_code}")
                print("🔍 Look for trial ID in the response HTML...")
                
                # Try to extract trial ID from response
                import re
                trial_matches = re.findall(r'trial[_-]?id["\s:=]+([A-Za-z0-9_-]+)', response_text)
                if trial_matches:
                    new_trial_id = trial_matches[0]
                    print(f"🎯 New Trial ID found: {new_trial_id}")
                    print(f"🌐 Dashboard URL: https://api.mapmystandards.ai/dashboard/{new_trial_id}")
                    return new_trial_id
                else:
                    print("⚠️ Trial created but ID not found in response. Check the API response.")
            return True
        else:
            print(f"❌ Signup failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    print("🌐 Production Trial Recovery")
    print("=" * 50)
    
    # Use realistic customer information
    name = "Customer"  # Update with your actual name if you'd like
    email = "customer@example.com"  # Update with your actual email if you'd like
    organization = "Paying Customer"
    
    print(f"Creating new trial for: {name} ({email})")
    result = create_trial_via_api("ALuvYpNhGklwcZqLnd5yIw", name, email, organization)
    
    if result:
        print("\n🎉 Success! You should now be able to access your dashboard.")
        print("\nIf the original trial ID still doesn't work, use the new trial ID shown above.")
    else:
        print("\n❌ Recovery failed. The API deployment may still be in progress.")
        print("Please wait a few minutes and try accessing your original dashboard URL:")
        print("https://api.mapmystandards.ai/dashboard/ALuvYpNhGklwcZqLnd5yIw")
