#!/usr/bin/env python3
"""
Test email sending with actual credentials
"""

import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os

def test_email_send():
    """Test sending an actual email with your credentials"""
    
    # Email configuration
    smtp_server = "mx1.titan.email"
    smtp_port = 587
    username = "support@mapmystandards.ai"
    password = "Ipo4Eva45*"
    
    print("🔍 Testing email sending with actual credentials...")
    print(f"   Server: {smtp_server}:{smtp_port}")
    print(f"   Username: {username}")
    
    try:
        # Create test message
        msg = MimeMultipart()
        msg['From'] = username
        msg['To'] = username  # Send to yourself for testing
        msg['Subject'] = "MapMyStandards.ai Email System Test"
        
        body = """
Hello!

This is a test email from your MapMyStandards.ai email system.

If you receive this email, your email configuration is working perfectly!

✅ SMTP connection: SUCCESS
✅ Authentication: SUCCESS  
✅ Email delivery: SUCCESS

Your email system is ready for production use.

Best regards,
MapMyStandards.ai Email System
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Connect and send
        print("   Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        print("   Starting TLS encryption...")
        server.starttls()
        
        print("   Authenticating...")
        server.login(username, password)
        
        print("   Sending email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ SUCCESS: Test email sent successfully!")
        print(f"   Check your inbox at {username}")
        print("\n🎉 Your email system is fully operational!")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("   Please check your email password")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ERROR: {e}")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("📧 MapMyStandards.ai Email Test with Credentials")
    print("=" * 60)
    
    success = test_email_send()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 RESULT: Email system is ready for production!")
        print("\n📝 Next steps:")
        print("1. Your contact forms will now work properly")
        print("2. Welcome emails will be sent to new users")
        print("3. Demo requests will be delivered to your inbox")
    else:
        print("⚠️  RESULT: Email configuration needs attention")
        print("\n🔧 Troubleshooting:")
        print("1. Verify the email account exists in your hosting panel")
        print("2. Check that the password is correct")
        print("3. Ensure the email account is properly activated")
