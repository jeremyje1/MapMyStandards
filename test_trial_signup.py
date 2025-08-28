#!/usr/bin/env python3
"""
Test script to verify trial signup is working
"""
import requests
import json

# API endpoint
API_URL = "https://api.mapmystandards.ai/api/trial/signup"

# Test signup data (simulating form submission)
test_data = {
    "name": "Test User",
    "institution_name": "Test University", 
    "email": "test-debug@example.com",
    "password": "testpassword123",
    "role": "administrator",
    "plan": "college_monthly",
    "payment_method_id": "pm_card_visa",  # Stripe test payment method
    "phone": "555-123-4567",
    "newsletter_opt_in": False
}

print("Testing trial signup API endpoint...")
print(f"URL: {API_URL}")
print(f"Data: {json.dumps(test_data, indent=2)}")
print()

try:
    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json"},
        json=test_data,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()
    
    try:
        result = response.json()
        print("Response JSON:")
        print(json.dumps(result, indent=2))
    except:
        print("Response Text:")
        print(response.text)
        
    if response.status_code == 200:
        print("\n✅ API endpoint is working!")
    else:
        print(f"\n❌ API endpoint returned error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error calling API: {e}")