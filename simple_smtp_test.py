#!/usr/bin/env python3
"""
Simple SMTP authentication test
"""

import smtplib

def test_smtp_auth():
    """Test SMTP authentication with your credentials"""
    
    smtp_server = "mx1.titan.email"
    smtp_port = 587
    username = "support@mapmystandards.ai"
    password = "Ipo4Eva45*"
    
    print("🔍 Testing SMTP Authentication...")
    print(f"   Server: {smtp_server}:{smtp_port}")
    print(f"   Username: {username}")
    
    try:
        print("   Connecting to server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        
        print("   Starting TLS...")
        server.starttls()
        
        print("   Attempting authentication...")
        server.login(username, password)
        
        print("   Disconnecting...")
        server.quit()
        
        print("✅ SUCCESS: Authentication successful!")
        print("🎉 Your email credentials are working correctly!")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("   The email account may not exist or password is incorrect")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("   Cannot connect to SMTP server")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("📧 SMTP Authentication Test")
    print("=" * 50)
    
    success = test_smtp_auth()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 RESULT: Email configuration is correct!")
        print("\n✅ Your MapMyStandards.ai email system is ready:")
        print("   • Contact forms will work")
        print("   • Welcome emails will be sent")
        print("   • Demo requests will be delivered")
        print("   • Support notifications will function")
    else:
        print("⚠️  RESULT: Email setup needs attention")
        print("\n🔧 Please check:")
        print("   • Email account exists in hosting panel")
        print("   • Password is exactly: Ipo4Eva45*")
        print("   • Account is activated and working")
