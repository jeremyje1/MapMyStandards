#!/usr/bin/env python3
"""
Test different username formats for Titan Email
"""

import smtplib

def test_username_formats():
    """Test different username formats"""
    
    server = "smtp.titan.email"
    port = 587
    password = "Ipo4Eva45*"
    
    username_formats = [
        "support@mapmystandards.ai",
        "support",
        "support%mapmystandards.ai",
        "mapmystandards.ai\\support"
    ]
    
    print(f"🔍 Testing Username Formats on {server}:{port}")
    print("=" * 50)
    
    for username in username_formats:
        print(f"\n--- Testing username: {username} ---")
        
        try:
            smtp = smtplib.SMTP(server, port, timeout=15)
            smtp.starttls()
            smtp.ehlo()
            
            print(f"   Attempting login with: {username}")
            smtp.login(username, password)
            print("   ✅ LOGIN SUCCESSFUL!")
            smtp.quit()
            return username
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Auth failed: {e}")
            try:
                smtp.quit()
            except:
                pass
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    print("📧 Titan Email Username Format Test")
    print("=" * 50)
    
    working_username = test_username_formats()
    
    print("\n" + "=" * 50)
    if working_username:
        print(f"🎉 SUCCESS: Working username format found!")
        print(f"   Username: {working_username}")
        print(f"   Server: smtp.titan.email:587")
    else:
        print("❌ No working username format found")
        print("\n💡 This suggests:")
        print("   1. Password may be incorrect")
        print("   2. Account needs activation in Namecheap")
        print("   3. Need to check account status in Titan webmail")
