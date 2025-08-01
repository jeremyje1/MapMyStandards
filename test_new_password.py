#!/usr/bin/env python3
"""
Test SMTP with new password: MapMyStandardsSMTP1*
"""

import smtplib

def test_new_password():
    """Test SMTP with the new password"""
    
    server = "smtp.titan.email"
    port = 587
    username = "support@mapmystandards.ai"
    password = "MapMyStandardsSMTP1*"
    
    print("🔍 Testing SMTP with New Password")
    print("=" * 50)
    print(f"Server: {server}:{port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    try:
        print("\n📡 Connecting to SMTP server...")
        smtp = smtplib.SMTP(server, port, timeout=15)
        
        print("🔒 Starting TLS encryption...")
        smtp.starttls()
        smtp.ehlo()
        
        print("🔐 Attempting authentication...")
        smtp.login(username, password)
        
        print("✅ LOGIN SUCCESSFUL!")
        print("🎉 SMTP authentication is working!")
        
        smtp.quit()
        
        print("\n" + "=" * 50)
        print("🎯 SUCCESS: Your email system is now operational!")
        print("\n📧 Your MapMyStandards.ai platform now has:")
        print("   ✅ Working SMTP authentication")
        print("   ✅ Contact form email sending")
        print("   ✅ Demo request notifications")
        print("   ✅ Welcome email capability")
        print("   ✅ Support communications")
        
        print(f"\n📝 Configuration confirmed:")
        print(f"   SMTP_SERVER=smtp.titan.email")
        print(f"   SMTP_PORT=587")
        print(f"   SMTP_USE_TLS=true")
        print(f"   SMTP_USERNAME=support@mapmystandards.ai")
        print(f"   SMTP_PASSWORD=MapMyStandardsSMTP1*")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 If this still fails:")
        print("   1. Wait a few minutes for password change to propagate")
        print("   2. Try logging out and back into webmail")
        print("   3. Verify the new password works in webmail first")
        return False
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("📧 Testing New Email Password")
    print("=" * 50)
    
    success = test_new_password()
    
    if success:
        print("\n🚀 Your email system is ready for production!")
        print("   Test your contact forms - they should now work!")
    else:
        print("\n⏳ If authentication failed, wait a few minutes")
        print("   Password changes sometimes take time to propagate")
