#!/usr/bin/env python3
"""
Quick Gmail SMTP setup for MapMyStandards.ai
Simple, free, and reliable email solution
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """Test Gmail SMTP configuration"""
    
    # Gmail SMTP settings
    server = "smtp.gmail.com"
    port = 587
    
    # You'll need to set these in your .env file
    username = input("Enter your Gmail address (e.g., mapmystandardsai@gmail.com): ")
    password = input("Enter your Gmail app password: ")
    
    print(f"\n🚀 Testing Gmail SMTP Setup")
    print("=" * 50)
    print(f"Server: {server}:{port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    try:
        print("\n📡 Connecting to Gmail SMTP...")
        smtp = smtplib.SMTP(server, port, timeout=10)
        
        print("🔒 Starting TLS encryption...")
        smtp.starttls()
        smtp.ehlo()
        
        print("🔐 Attempting authentication...")
        smtp.login(username, password)
        
        print("✅ AUTHENTICATION SUCCESSFUL!")
        
        # Test sending email
        print("📧 Testing email send...")
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # Send to self
        msg['Subject'] = "MapMyStandards.ai - Gmail SMTP Test"
        
        body = """
🎉 Gmail SMTP Test Successful!

Your MapMyStandards.ai email system is now operational with Gmail SMTP.

Capabilities enabled:
✅ Contact form submissions
✅ Demo request notifications  
✅ Welcome emails
✅ Support communications
✅ Password reset emails

Professional email delivery for your SaaS platform!

Best regards,
MapMyStandards.ai System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        smtp.sendmail(username, [username], msg.as_string())
        print("✅ Test email sent successfully!")
        
        smtp.quit()
        
        print("\n🎯 Gmail SMTP Configuration Working!")
        print("✅ Your MapMyStandards.ai email system is operational")
        print("📧 Check your Gmail inbox for the test email")
        
        print(f"\n📝 Add these settings to your .env file:")
        print(f"SMTP_SERVER=smtp.gmail.com")
        print(f"SMTP_PORT=587")
        print(f"SMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD={password}")
        print(f"SMTP_USE_TLS=true")
        print(f"EMAIL_FROM={username}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Gmail SMTP requires an app password:")
        print("1. 🌐 Go to: https://myaccount.google.com")
        print("2. 🔐 Security → 2-Step Verification (enable if not already)")
        print("3. 🔑 Security → App passwords → Generate app password")
        print("4. 📝 Use the generated app password, not your regular password")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def gmail_setup_guide():
    """Print Gmail setup instructions"""
    
    print("📧 Gmail SMTP Setup Guide for MapMyStandards.ai")
    print("=" * 60)
    print()
    print("🎯 Why Gmail SMTP?")
    print("   ✅ Completely free")
    print("   ✅ Reliable delivery")
    print("   ✅ No account limits")
    print("   ✅ Quick 5-minute setup")
    print()
    print("📝 Setup Steps:")
    print("1. 📧 Create Gmail account: mapmystandardsai@gmail.com")
    print("2. 🔐 Enable 2-factor authentication:")
    print("   https://myaccount.google.com/security")
    print("3. 🔑 Generate app password:")
    print("   Security → App passwords → Mail → Generate")
    print("4. 📝 Save the 16-character app password")
    print("5. 🧪 Run this test script")
    print()
    print("🚀 Ready to test? Run the authentication test!")

if __name__ == "__main__":
    print("🚀 MapMyStandards.ai - Gmail SMTP Setup")
    print()
    
    choice = input("Choose: (1) Setup Guide (2) Test Authentication: ")
    
    if choice == "1":
        gmail_setup_guide()
        print("\n💡 After setup, run: python test_gmail_smtp.py")
        print("   Then choose option 2 to test authentication")
    elif choice == "2":
        success = test_gmail_smtp()
        if success:
            print("\n🚀 Your email system is production-ready!")
            print("🎉 MapMyStandards.ai can now send emails reliably!")
        else:
            print("\n📞 Follow the app password instructions above")
    else:
        print("Invalid choice. Run the script again and choose 1 or 2.")
