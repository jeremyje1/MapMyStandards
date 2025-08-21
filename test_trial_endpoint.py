#!/usr/bin/env python3
"""
Test the trial signup endpoint directly
"""

import requests
import json
from datetime import datetime

def test_trial_signup():
    """Test the trial signup endpoint"""
    print("🧪 TESTING TRIAL SIGNUP ENDPOINT")
    print("=" * 50)
    
    # Test data
    test_data = {
        "institution_name": "Test University",
        "email": "test@example.com",
        "role": "Director of Accreditation",
        "plan": "starter",
        "payment_method_id": "pm_card_visa",  # Stripe test payment method
        "phone": "555-0123",
        "newsletter_opt_in": True
    }
    
    print("📤 Request Data:")
    print(json.dumps(test_data, indent=2))
    print()
    
    # Test production endpoint
    url = "https://platform.mapmystandards.ai/api/v1/billing/trial/signup"
    
    print(f"🌐 Testing: {url}")
    print("-" * 50)
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success Response:")
            print(json.dumps(result, indent=2))
            
            # Check response structure
            print("\n🔍 Response Analysis:")
            if "data" in result:
                data = result["data"]
                print(f"   - Subscription ID: {data.get('subscription_id', 'NOT FOUND')}")
                print(f"   - Customer ID: {data.get('customer_id', 'NOT FOUND')}")
                print(f"   - Trial End: {data.get('trial_end', 'NOT FOUND')}")
                print(f"   - API Key: {data.get('api_key', 'NOT FOUND')[:20]}..." if data.get('api_key') else "   - API Key: NOT FOUND")
            else:
                print("   ⚠️  No 'data' field in response")
                
        else:
            print(f"❌ Error Response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request Failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("💡 Notes:")
    print("- Using test payment method 'pm_card_visa'")
    print("- In production, use real Stripe payment method IDs")
    print("- Check Railway logs for detailed error messages")

if __name__ == "__main__":
    test_trial_signup()
