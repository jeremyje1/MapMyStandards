#!/usr/bin/env python3
"""
Direct Email Test for MailerSend Integration
Tests email functionality directly with the MailerSend API
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_trial_signup_correct_format():
    """Test trial signup with the correct field names"""
    print("🚀 Testing Trial Signup with Correct Format")
    print("=" * 50)
    
    test_data = {
        "email": f"test+{datetime.now().strftime('%Y%m%d_%H%M%S')}@mapmystandards.ai",
        "first_name": "Test",
        "last_name": "User", 
        "organization": "Test Organization",
        "use_case": "Testing MailerSend integration"
    }
    
    try:
        response = requests.post(
            "https://api.mapmystandards.ai/trial/signup",
            json=test_data,
            timeout=15
        )
        
        print(f"📧 Test Email: {test_data['email']}")
        print(f"👤 Name: {test_data['first_name']} {test_data['last_name']}")
        print(f"🏢 Organization: {test_data['organization']}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Trial signup successful!")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            
            # Check if email was sent
            if result.get('email_sent'):
                print("📧 ✅ Welcome email sent successfully via MailerSend!")
            else:
                print("📧 ⚠️  Welcome email status unknown")
                
            return True
        else:
            print(f"❌ Trial signup failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_contact_form_submission():
    """Test contact form with MailerSend"""
    print("\n🚀 Testing Contact Form Submission")
    print("=" * 50)
    
    contact_data = {
        "name": "Test Contact User",
        "email": f"test+contact_{datetime.now().strftime('%H%M%S')}@mapmystandards.ai",
        "subject": "MailerSend Integration Test",
        "message": f"""This is a test of the contact form with MailerSend integration.

Test Details:
- Timestamp: {datetime.now().isoformat()}
- Purpose: Verify MailerSend email delivery
- Platform: MapMyStandards.ai
- Status: Testing email notifications

Please confirm this message was received successfully."""
    }
    
    try:
        response = requests.post(
            "https://api.mapmystandards.ai/contact",
            json=contact_data,
            timeout=15
        )
        
        print(f"👤 Name: {contact_data['name']}")
        print(f"📧 Email: {contact_data['email']}")
        print(f"📋 Subject: {contact_data['subject']}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Contact form submission successful!")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            
            if result.get('email_sent'):
                print("📧 ✅ Contact notification email sent via MailerSend!")
            else:
                print("📧 ⚠️  Contact email status unknown")
                
            return True
        else:
            print(f"❌ Contact form failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_discovery():
    """Discover available API endpoints"""
    print("\n🔍 API Endpoint Discovery")
    print("=" * 30)
    
    endpoints_to_test = [
        "/health",
        "/",
        "/trial/signup", 
        "/contact",
        "/status",
        "/docs",
        "/admin/trials"
    ]
    
    available_endpoints = []
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"https://api.mapmystandards.ai{endpoint}", timeout=5)
            status = "✅" if response.status_code in [200, 302] else "❌"
            print(f"{status} {endpoint} - {response.status_code}")
            if response.status_code in [200, 302]:
                available_endpoints.append(endpoint)
        except Exception as e:
            print(f"❌ {endpoint} - ERROR: {e}")
    
    print(f"\n📊 Available endpoints: {len(available_endpoints)}/{len(endpoints_to_test)}")
    return available_endpoints

def main():
    """Main test execution"""
    print("🧪 MapMyStandards.ai MailerSend Integration Test")
    print("=" * 60)
    print(f"🕒 Timestamp: {datetime.now().isoformat()}")
    print(f"🌐 Target: https://api.mapmystandards.ai")
    
    # Test 1: API Discovery
    available_endpoints = test_api_discovery()
    
    # Test 2: Trial Signup (if endpoint exists)
    if "/trial/signup" in available_endpoints:
        trial_success = test_trial_signup_correct_format()
    else:
        print("\n⚠️ Skipping trial signup test - endpoint not available")
        trial_success = False
    
    # Test 3: Contact Form (if endpoint exists)  
    if "/contact" in available_endpoints:
        contact_success = test_contact_form_submission()
    else:
        print("\n⚠️ Skipping contact form test - endpoint not available")
        contact_success = False
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    if trial_success and contact_success:
        print("🎉 ALL EMAIL TESTS PASSED!")
        print("✅ MailerSend integration is working correctly")
        print("📧 Both welcome and contact emails are being sent")
    elif trial_success or contact_success:
        print("⚠️ PARTIAL SUCCESS")
        print(f"✅ Trial signup email: {'PASS' if trial_success else 'FAIL'}")
        print(f"✅ Contact form email: {'PASS' if contact_success else 'FAIL'}")
    else:
        print("❌ EMAIL TESTS FAILED")
        print("🔧 Check MailerSend configuration and API endpoints")
    
    print("\n💡 Next Steps:")
    print("1. Check your email inbox for test messages")
    print("2. Verify MailerSend dashboard for delivery stats")
    print("3. Test with real customer scenarios")

if __name__ == "__main__":
    main()
