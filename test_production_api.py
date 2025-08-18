#!/usr/bin/env python3
"""
Quick Production API Test - Test the correct field format for trial signup
"""

import requests
import json
from datetime import datetime

def test_production_trial_signup():
    """Test production API with correct field format"""
    
    print("🧪 Testing Production Trial Signup with Correct Format")
    print("=" * 60)
    
    # Test with the correct field structure
    test_data = {
        "email": f"test+{datetime.now().strftime('%Y%m%d_%H%M%S')}@mapmystandards.ai",
        "first_name": "Test",
        "last_name": "User",
        "institution_name": "Test Organization",
        "plan": "free",
        "use_case": "Testing production API format"
    }
    
    print(f"📧 Email: {test_data['email']}")
    print(f"👤 Name: {test_data['first_name']} {test_data['last_name']}")
    print(f"🏢 Institution: {test_data['institution_name']}")
    
    try:
        print("\n🚀 Sending request to production API...")
        response = requests.post(
            "https://api.mapmystandards.ai/trial/signup",
            json=test_data,
            timeout=15
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Trial signup worked!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            if result.get('email_sent'):
                print("📧 ✅ Email was sent!")
                print("🎯 MailerSend integration is working!")
            else:
                print("📧 ⚠️ Email was not sent (check MailerSend config)")
            
            return True
            
        elif response.status_code == 400:
            print("❌ FAILED: Bad Request")
            try:
                error_data = response.json()
                print(f"📝 Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📝 Error Text: {response.text}")
            return False
            
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_contact_form():
    """Test contact form submission"""
    
    print("\n🧪 Testing Contact Form")
    print("=" * 40)
    
    contact_data = {
        "name": "Test Contact",
        "email": f"contact+{datetime.now().strftime('%H%M%S')}@mapmystandards.ai",
        "subject": "Production API Test",
        "message": "Testing contact form with production API"
    }
    
    print(f"👤 Name: {contact_data['name']}")
    print(f"📧 Email: {contact_data['email']}")
    
    try:
        print("\n🚀 Sending contact form...")
        response = requests.post(
            "https://api.mapmystandards.ai/contact",
            json=contact_data,
            timeout=15
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Contact form worked!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Quick Production API Test")
    print("=" * 50)
    
    # Test trial signup
    trial_success = test_production_trial_signup()
    
    # Test contact form  
    contact_success = test_contact_form()
    
    # Summary
    print("\n" + "="*50)
    print("📋 SUMMARY")
    print("="*50)
    print(f"Trial Signup: {'✅ PASS' if trial_success else '❌ FAIL'}")
    print(f"Contact Form: {'✅ PASS' if contact_success else '❌ FAIL'}")
    
    if trial_success and contact_success:
        print("\n🎉 PRODUCTION API IS WORKING!")
        print("✅ Customer flow is operational")
    elif trial_success:
        print("\n⚠️ PARTIAL SUCCESS")
        print("✅ Trial signup working")
        print("❌ Contact form needs attention")
    else:
        print("\n❌ API ISSUES DETECTED")
        print("🔧 Check API deployment and endpoints")
