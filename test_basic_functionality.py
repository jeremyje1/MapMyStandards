#!/usr/bin/env python3
"""
Test the contact form and other endpoints that should work without SMTP
"""

import requests
import json

# Production backend URL
BACKEND_URL = "https://api.mapmystandards.ai"

def test_contact_form():
    """Test contact form submission"""
    print("🧪 Testing Contact Form...")
    
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Message",
        "message": "This is a test message to verify the contact form works."
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/contact", json=test_data, timeout=15)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Contact Form Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Contact form failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_basic_endpoints():
    """Test basic endpoints"""
    print("🧪 Testing Basic Endpoints...")
    
    endpoints = [
        "/health",
        "/",
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=15)
            print(f"{endpoint}: {response.status_code}")
            results[endpoint] = response.status_code == 200
        except Exception as e:
            print(f"{endpoint}: ERROR - {str(e)}")
            results[endpoint] = False
    
    return results

def main():
    """Run basic tests"""
    print("🚀 Testing Basic Platform Functionality")
    print(f"🎯 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    # Test basic endpoints
    endpoint_results = test_basic_endpoints()
    
    print("\n" + "=" * 60)
    
    # Test contact form
    contact_ok = test_contact_form()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for endpoint, result in endpoint_results.items():
        status = "✅ OK" if result else "❌ FAIL"
        print(f"{endpoint:<20} {status}")
    
    print(f"Contact Form:        {'✅ OK' if contact_ok else '❌ FAIL'}")
    
    print("\n📧 NEXT STEPS:")
    print("1. Generate NEW MailerSend SMTP credentials (rotate exposed ones)")
    print("2. Add SMTP environment variables to Railway:")
    print("   - SMTP_SERVER=smtp.mailersend.net")
    print("   - SMTP_PORT=587")
    print("   - SMTP_USERNAME=<new_username>")
    print("   - SMTP_PASSWORD=<new_password>")
    print("   - FROM_NAME=MapMyStandards")
    print("   - MAILERSEND_TRIAL=false (since domain is verified)")
    print("3. Redeploy Railway service")
    print("4. Test email functionality")

if __name__ == "__main__":
    main()
