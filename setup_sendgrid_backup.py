#!/usr/bin/env python3
"""
Setup SendGrid as backup email service for MapMyStandards.ai
More reliable than Titan Email for transactional emails
"""

import os
import requests
import json

def setup_sendgrid_guide():
    """Generate guide for setting up SendGrid"""
    
    guide = """
# 🚀 SendGrid Setup for MapMyStandards.ai (Backup Solution)

## Why SendGrid?
- ✅ 100 emails/day free
- ✅ Reliable delivery
- ✅ No password issues
- ✅ Great for SaaS platforms
- ✅ Better deliverability than Titan

## Setup Steps

### 1. Create SendGrid Account
1. 🌐 Go to: https://sendgrid.com
2. 📝 Sign up with your email
3. ✅ Verify your account

### 2. Get API Key
1. 🔐 Login to SendGrid dashboard
2. 📧 Go to: Settings → API Keys
3. 🔑 Create API Key:
   - Name: `MapMyStandards Production`
   - Permissions: `Full Access` (or `Mail Send` only)
4. 💾 **COPY AND SAVE THE API KEY** - you won't see it again!

### 3. Verify Domain (Optional but Recommended)
1. 🌐 Go to: Settings → Sender Authentication
2. 📧 Add domain: `mapmystandards.ai`
3. 📝 Add the DNS records they provide to Namecheap
4. ✅ Verify domain

### 4. Update Your Configuration

Add to your `.env` file:
```bash
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
EMAIL_FROM=support@mapmystandards.ai
EMAIL_FROM_NAME=MapMyStandards Support

# Keep Titan as backup
SMTP_SERVER=smtp.titan.email
SMTP_PORT=587
SMTP_USERNAME=support@mapmystandards.ai
SMTP_PASSWORD=your_titan_app_password
```

### 5. Install SendGrid Python Library
```bash
pip install sendgrid
```

### 6. Test SendGrid
Run the test script below to confirm it works.

## ✅ Benefits of This Setup
- 🎯 Primary: SendGrid (reliable, fast)
- 🔄 Backup: Titan Email (if SendGrid fails)
- 📧 Same from address: support@mapmystandards.ai
- 🔒 Professional delivery
- 📊 Email analytics and tracking

## 🎉 Result
Your MapMyStandards.ai will have:
- ✅ Reliable contact form emails
- ✅ Demo request notifications  
- ✅ Welcome emails for new users
- ✅ Password reset emails
- ✅ Support communications
- ✅ 99.9% delivery rate
"""
    
    return guide

def create_sendgrid_test():
    """Create test script for SendGrid"""
    
    test_script = '''#!/usr/bin/env python3
"""
Test SendGrid integration for MapMyStandards.ai
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def test_sendgrid():
    """Test SendGrid email sending"""
    
    # Get API key from environment
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment")
        print("💡 Add it to your .env file:")
        print("   SENDGRID_API_KEY=your_api_key_here")
        return False
    
    try:
        print("🚀 Testing SendGrid Integration")
        print("=" * 50)
        
        # Create the email
        message = Mail(
            from_email='support@mapmystandards.ai',
            to_emails='support@mapmystandards.ai',  # Send to self for testing
            subject='MapMyStandards.ai - SendGrid Test Email',
            html_content='''
            <h2>🎉 SendGrid Test Successful!</h2>
            <p>Your MapMyStandards.ai email system is now operational with SendGrid.</p>
            <p><strong>Capabilities enabled:</strong></p>
            <ul>
                <li>✅ Contact form submissions</li>
                <li>✅ Demo request notifications</li>
                <li>✅ Welcome emails</li>
                <li>✅ Support communications</li>
            </ul>
            <p>Professional email delivery for your SaaS platform!</p>
            '''
        )
        
        # Send the email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        print(f"✅ Email sent successfully!")
        print(f"📧 Status code: {response.status_code}")
        print(f"📝 Response: Success")
        
        print("\\n🎯 SendGrid Configuration Working!")
        print("✅ Your MapMyStandards.ai email system is operational")
        print("📧 Check your inbox for the test email")
        
        return True
        
    except Exception as e:
        print(f"❌ SendGrid test failed: {e}")
        print("\\n🔧 Troubleshooting:")
        print("1. ✅ Verify your API key is correct")
        print("2. 🌐 Check SendGrid dashboard for account status")
        print("3. 📧 Ensure sender email is verified")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_sendgrid()
    
    if success:
        print("\\n🚀 Your email system is production-ready!")
        print("🎉 MapMyStandards.ai can now send emails reliably!")
    else:
        print("\\n📞 Need help? Check the SendGrid dashboard or contact support")
'''
    
    return test_script

def main():
    """Generate SendGrid setup files"""
    
    print("🚀 Generating SendGrid Backup Solution")
    print("=" * 50)
    
    # Create guide
    guide_content = setup_sendgrid_guide()
    with open('SENDGRID_SETUP_GUIDE.md', 'w') as f:
        f.write(guide_content)
    print("✅ Created: SENDGRID_SETUP_GUIDE.md")
    
    # Create test script
    test_content = create_sendgrid_test()
    with open('test_sendgrid.py', 'w') as f:
        f.write(test_content)
    print("✅ Created: test_sendgrid.py")
    
    print("\\n🎯 Next Steps:")
    print("1. 📖 Read: SENDGRID_SETUP_GUIDE.md")
    print("2. 🌐 Sign up at SendGrid.com")
    print("3. 🔑 Get your API key")
    print("4. 📝 Add SENDGRID_API_KEY to your .env file")
    print("5. 🧪 Run: python test_sendgrid.py")
    
    print("\\n💡 This gives you a reliable email solution while you")
    print("   work on getting the Titan Email app password!")

if __name__ == "__main__":
    main()
