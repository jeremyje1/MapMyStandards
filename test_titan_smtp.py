#!/usr/bin/env python3
"""
Test alternative SMTP servers for Titan Email
"""

import smtplib

def test_alternative_smtp_servers():
    """Test different SMTP server configurations"""
    
    servers_to_test = [
        ("smtp.titan.email", 587),
        ("smtp.titan.email", 465),
        ("outbound.titan.email", 587),
        ("mail.mapmystandards.ai", 587),
        ("mail.mapmystandards.ai", 465),
        ("smtp.mapmystandards.ai", 587)
    ]
    
    username = "support@mapmystandards.ai"
    password = "Ipo4Eva45*"
    
    print("🔍 Testing Alternative SMTP Servers for Titan Email...")
    print("=" * 60)
    
    for server, port in servers_to_test:
        print(f"\n--- Testing {server}:{port} ---")
        
        try:
            print(f"   Connecting to {server}:{port}...")
            smtp = smtplib.SMTP(server, port, timeout=15)
            
            print("   Connected! Getting server capabilities...")
            response = smtp.ehlo()
            print(f"   Server response: {response[1].decode().split()[0] if response[1] else 'No response'}")
            
            # Check if STARTTLS is available
            if smtp.has_extn('STARTTLS'):
                print("   ✅ STARTTLS supported - enabling...")
                smtp.starttls()
                smtp.ehlo()  # Re-identify after STARTTLS
            else:
                print("   ⚠️  STARTTLS not supported")
            
            # Check AUTH capability
            if smtp.has_extn('AUTH'):
                print("   ✅ AUTH supported")
                auth_methods = smtp.esmtp_features.get('auth', '').split()
                print(f"   Available auth methods: {auth_methods}")
                
                try:
                    print("   Attempting login...")
                    smtp.login(username, password)
                    print("   ✅ LOGIN SUCCESSFUL!")
                    smtp.quit()
                    return server, port
                except Exception as auth_e:
                    print(f"   ❌ Login failed: {auth_e}")
            else:
                print("   ❌ AUTH not supported")
            
            smtp.quit()
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    
    return None, None

if __name__ == "__main__":
    print("📧 Titan Email SMTP Server Discovery")
    print("=" * 60)
    
    working_server, working_port = test_alternative_smtp_servers()
    
    print("\n" + "=" * 60)
    if working_server:
        print(f"🎉 SUCCESS: Found working SMTP server!")
        print(f"   Server: {working_server}:{working_port}")
        print(f"\n📝 Update your .env file with:")
        print(f"   SMTP_SERVER={working_server}")
        print(f"   SMTP_PORT={working_port}")
    else:
        print("❌ No working SMTP servers found")
        print("\n💡 Next steps:")
        print("   1. Fix SPF records in Namecheap (remove duplicate)")
        print("   2. Check Titan Email documentation for correct SMTP settings")
        print("   3. Contact Namecheap support for Titan Email SMTP details")
