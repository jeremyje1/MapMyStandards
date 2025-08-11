#!/usr/bin/env python3
"""
Complete Customer Flow & MailerSend Integration Test
Run this after configuring MailerSend SMTP settings
"""

import requests
import json
import time
from datetime import datetime
import uuid

def test_complete_customer_flow():
    """Test the complete customer flow with MailerSend"""
    
    print("🚀 MapMyStandards.ai Complete Customer Flow Test")
    print("=" * 70)
    print(f"🕒 Timestamp: {datetime.now().isoformat()}")
    print(f"📧 Testing with MailerSend Integration")
    
    test_id = str(uuid.uuid4())[:8]
    test_results = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "results": {}
    }
    
    # Test both production and local if available
    environments = [
        ("Production", "https://api.mapmystandards.ai"),
        ("Local", "http://localhost:8001")
    ]
    
    for env_name, base_url in environments:
        print(f"\n🌍 Testing {env_name} Environment")
        print("=" * 50)
        print(f"🌐 URL: {base_url}")
        
        env_results = test_environment(base_url, test_id)
        test_results["results"][env_name.lower()] = env_results
        
        if env_results["available"]:
            print(f"\n📊 {env_name} Summary:")
            print(f"   API Health: {'✅' if env_results['health'] else '❌'}")
            print(f"   Trial Signup: {'✅' if env_results['trial_signup'] else '❌'}")
            print(f"   Trial Email: {'✅' if env_results['trial_email_sent'] else '❌'}")
            print(f"   Contact Form: {'✅' if env_results['contact_form'] else '❌'}")
            print(f"   Contact Email: {'✅' if env_results['contact_email_sent'] else '❌'}")
        else:
            print(f"⚠️  {env_name} environment not available")
    
    # Overall summary
    print("\n" + "="*70)
    print("🎯 OVERALL TEST SUMMARY")
    print("="*70)
    
    prod_results = test_results["results"].get("production", {})
    local_results = test_results["results"].get("local", {})
    
    # Check if emails are working in any environment
    email_working = False
    if prod_results.get("available"):
        email_working = prod_results.get("trial_email_sent") or prod_results.get("contact_email_sent")
    if local_results.get("available"):
        email_working = email_working or local_results.get("trial_email_sent") or local_results.get("contact_email_sent")
    
    if email_working:
        print("🎉 MailerSend Integration: ✅ WORKING!")
        print("📧 Emails are being sent successfully")
        print("✅ Customer flow is fully operational")
    else:
        print("⚠️  MailerSend Integration: ❌ NOT WORKING")
        print("📧 Email delivery needs configuration")
        print("🔧 Required: Update MailerSend SMTP settings")
    
    print("\n💡 Recommendations:")
    if not email_working:
        print("1. 🔧 Configure MailerSend SMTP settings in environment variables")
        print("2. 📧 Update SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD")
        print("3. 🚀 Redeploy with updated configuration")
        print("4. 🧪 Run this test again to verify")
    else:
        print("1. ✅ Email system is working correctly")
        print("2. 📊 Monitor MailerSend dashboard for delivery stats")
        print("3. 🎯 Test with real customer scenarios")
        print("4. 📈 Set up email delivery monitoring")
    
    # Save results
    filename = f"complete_customer_flow_test_{test_id}.json"
    with open(filename, "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Full test results saved to: {filename}")
    
    return email_working

def test_environment(base_url, test_id):
    """Test a specific environment"""
    results = {
        "available": False,
        "health": False,
        "trial_signup": False,
        "trial_email_sent": False,
        "contact_form": False,
        "contact_email_sent": False,
        "errors": []
    }
    
    # Test 1: Health Check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            results["available"] = True
            results["health"] = True
            print("✅ API Health: Working")
        else:
            print(f"❌ API Health: Failed ({response.status_code})")
            return results
    except Exception as e:
        print(f"❌ API Health: Connection failed - {e}")
        return results
    
    # Test 2: Trial Signup
    trial_data = {
        "email": f"test+trial_{test_id}@mapmystandards.ai",
        "first_name": f"Test",
        "last_name": f"Trial{test_id}",
        "organization": "Test Organization",
        "use_case": "Testing MailerSend integration"
    }
    
    try:
        response = requests.post(f"{base_url}/trial/signup", json=trial_data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            results["trial_signup"] = True
            results["trial_email_sent"] = result.get("email_sent", False)
            print(f"✅ Trial Signup: Success (Email: {'✅' if result.get('email_sent') else '❌'})")
        else:
            print(f"❌ Trial Signup: Failed ({response.status_code})")
            results["errors"].append(f"Trial signup: {response.status_code}")
    except Exception as e:
        print(f"❌ Trial Signup: Error - {e}")
        results["errors"].append(f"Trial signup: {e}")
    
    # Test 3: Contact Form
    contact_data = {
        "name": f"Test Contact {test_id}",
        "email": f"test+contact_{test_id}@mapmystandards.ai",
        "subject": "MailerSend Integration Test",
        "message": f"Test message from customer flow test {test_id}"
    }
    
    try:
        response = requests.post(f"{base_url}/contact", json=contact_data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            results["contact_form"] = True
            results["contact_email_sent"] = result.get("email_sent", False)
            print(f"✅ Contact Form: Success (Email: {'✅' if result.get('email_sent') else '❌'})")
        else:
            print(f"❌ Contact Form: Failed ({response.status_code})")
            results["errors"].append(f"Contact form: {response.status_code}")
    except Exception as e:
        print(f"❌ Contact Form: Error - {e}")
        results["errors"].append(f"Contact form: {e}")
    
    return results

def show_mailersend_config_help():
    """Show help for configuring MailerSend"""
    print("\n" + "="*60)
    print("📧 MailerSend Configuration Guide")
    print("="*60)
    print("""
To configure MailerSend for email delivery, add these environment variables:

🔧 Required Environment Variables:
SMTP_SERVER=smtp.mailersend.net
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_mailersend_username
SMTP_PASSWORD=your_mailersend_password

📝 How to set up:
1. Log into your MailerSend dashboard
2. Go to Settings > SMTP
3. Create or copy your SMTP credentials
4. Update your environment configuration
5. Redeploy your application
6. Run this test again to verify

🔗 MailerSend Documentation:
https://developers.mailersend.com/smtp/
""")

if __name__ == "__main__":
    print("🧪 Starting Complete Customer Flow Test")
    
    # Check if this is first run (show config help)
    try:
        with open("EMAIL_TEST_SUMMARY.md", "r") as f:
            if "❌ Needs configuration" in f.read():
                show_mailersend_config_help()
    except:
        pass
    
    success = test_complete_customer_flow()
    
    if not success:
        show_mailersend_config_help()
    
    exit(0 if success else 1)
