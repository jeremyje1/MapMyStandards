#!/usr/bin/env python3
"""
Production API Test - Using the CORRECT endpoint and field structure
Tests the actual Flask app deployed to Railway
"""

import requests
import json
from datetime import datetime
import secrets

def test_actual_production_api():
    """Test the real production API with correct endpoint and fields"""
    
    print("🎯 Testing ACTUAL Production API (Flask/subscription_backend.py)")
    print("=" * 70)
    
    # Use the CORRECT endpoint and field structure (snake_case)
    # Test with proper camelCase fields as required by backend
    test_data = {
        "firstName": "Test",
        "lastName": "User",
        "email": f"test+{datetime.now().strftime('%Y%m%d_%H%M%S')}@mapmystandards.ai",
        "institution": "Test Organization",
        "username": f"testuser{datetime.now().strftime('%H%M%S')}",
        "password": "TestPassword123!",
        "plan": "monthly"  # lowercase as required
    }

    print(f"📧 Email: {test_data['email']}")
    print(f"👤 Name: {test_data['firstName']} {test_data['lastName']}")
    print(f"🏢 Institution: {test_data['institution']}")
    print(f"👤 Username: {test_data['username']}")
    print(f"💳 Plan: {test_data['plan']}")
    
    try:
        print("\n🚀 Testing /create-trial-account endpoint...")
        response = requests.post(
            "https://api.mapmystandards.ai/create-trial-account",
            json=test_data,
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Trial account creation worked!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            # Check if this creates a Stripe checkout or handles trial differently
            if 'checkout_url' in result:
                print("💳 Stripe checkout URL created - this is a paid signup flow")
            elif 'trial_id' in result:
                print("🆓 Free trial created successfully")
            
            return True
            
        elif response.status_code == 400:
            print("❌ FAILED: Bad Request")
            try:
                error_data = response.json()
                print(f"📝 Error Details: {json.dumps(error_data, indent=2)}")
                
                # Suggest fixes for common errors
                if 'plan' in str(error_data):
                    print("\n💡 Plan issue - trying 'annual' instead...")
                    return test_with_annual_plan(test_data)
                elif 'email' in str(error_data):
                    print("💡 Email validation issue")
                elif 'password' in str(error_data):
                    print("💡 Password validation issue")
                    
            except:
                print(f"📝 Error Text: {response.text}")
            return False
            
        elif response.status_code == 404:
            print("❌ FAILED: Endpoint not found")
            print("🔧 The Flask app might not be deployed correctly")
            return False
            
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_with_annual_plan(original_data):
    """Try the same request with annual plan"""
    test_data = original_data.copy()
    test_data['plan'] = 'annual'
    test_data['email'] = f"test+annual_{datetime.now().strftime('%H%M%S')}@mapmystandards.ai"
    
    print(f"\n🔄 Retrying with plan: {test_data['plan']}")
    
    try:
        response = requests.post(
            "https://api.mapmystandards.ai/create-trial-account",
            json=test_data,
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS with annual plan!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Annual plan also failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📝 Error Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_other_endpoints():
    """Test other available endpoints"""
    print("\n🔍 Testing Other Available Endpoints")
    print("=" * 40)
    
    endpoints_to_test = [
        "/",
        "/health", 
        "/debug-config",
        "/test-email"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"https://api.mapmystandards.ai{endpoint}", timeout=5)
            status = "✅" if response.status_code in [200, 302] else "❌"
            print(f"{status} {endpoint} - {response.status_code}")
            
            if endpoint == "/debug-config" and response.status_code == 200:
                try:
                    config_data = response.json()
                    print(f"   📧 Email config: {config_data.get('email_configured', 'Unknown')}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ {endpoint} - ERROR: {e}")

if __name__ == "__main__":
    print("🧪 Production API Test - Flask App (subscription_backend.py)")
    print("=" * 70)
    
    # Test the actual production endpoints
    success = test_actual_production_api()
    
    # Test other endpoints for debugging
    test_other_endpoints()
    
    # Summary
    print("\n" + "="*70)
    print("📋 PRODUCTION API TEST SUMMARY")  
    print("="*70)
    
    if success:
        print("🎉 PRODUCTION API IS WORKING!")
        print("✅ Trial account creation successful")
        print("📧 Check your email for notifications")
        print("💡 Next: Test email functionality with MailerSend")
    else:
        print("❌ PRODUCTION API ISSUES")
        print("🔧 Check the endpoint structure and field requirements")
        print("📋 Review the Flask app deployment")
    
    print(f"\n💡 The production API is using subscription_backend.py (Flask)")
    print(f"📍 Correct endpoint: /create-trial-account")
    print(f"📝 Required fields: firstName, lastName, email, institution, username, password, plan")
    
    exit(0 if success else 1)
