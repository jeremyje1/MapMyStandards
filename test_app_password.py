#!/usr/bin/env python3
"""
Test SMTP with app-specific password input
"""

import smtplib
import getpass

def test_with_app_password():
    """Test SMTP with user-provided app-specific password"""
    
    server = "smtp.titan.email"
    port = 587
    username = "support@mapmystandards.ai"
    
    print("🔑 Testing SMTP with App-Specific Password")
    print("=" * 60)
    print(f"Server: {server}:{port}")
    print(f"Username: {username}")
    print()
    print("💡 If you have generated an app-specific password in your")
    print("   Titan Email dashboard, enter it below. Otherwise, try")
    print("   your regular password first.")
    print()
    
    # Get password from user
    test_password = getpass.getpass("Enter password (app-specific or regular): ")
    
    print(f"\n🔍 Testing authentication...")
    
    try:
        smtp = smtplib.SMTP(server, port, timeout=15)
        smtp.starttls()
        smtp.ehlo()
        
        print("   Attempting login...")
        smtp.login(username, test_password)
        print("   ✅ LOGIN SUCCESSFUL!")
        
        smtp.quit()
        
        print("\n🎉 SUCCESS! SMTP is working!")
        print(f"\n📝 Update your .env file:")
        print(f"SMTP_SERVER={server}")
        print(f"SMTP_PORT={port}")
        print(f"SMTP_USE_TLS=true")
        print(f"SMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD={test_password}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Auth failed: {e}")
        print(f"\n💡 Try these steps:")
        print(f"   1. Check if 2FA is enabled on your account")
        print(f"   2. Generate app-specific password in Titan Email settings")
        print(f"   3. Look for 'App Passwords' or 'Application Passwords'")
        print(f"   4. Contact Namecheap if you can't find these options")
        return False
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def main():
    print("📧 Titan Email App-Specific Password Test")
    print("=" * 60)
    
    success = test_with_app_password()
    
    if not success:
        print(f"\n📞 Need help? Contact Namecheap:")
        print(f"   Live Chat: https://www.namecheap.com/help-center/live-chat/")
        print(f"   Ask: 'How do I generate an app password for Titan Email SMTP?'")

if __name__ == "__main__":
    main()
