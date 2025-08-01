#!/usr/bin/env python3
"""
Extended SMTP testing with different methods
"""

import smtplib
import socket

def test_smtp_detailed():
    """Detailed SMTP testing"""
    
    servers_to_test = [
        ("mx1.titan.email", 587),
        ("mx1.titan.email", 25),
        ("mx1.titan.email", 465),
        ("mx2.titan.email", 587)
    ]
    
    username = "support@mapmystandards.ai"
    password = "Ipo4Eva45*"
    
    print("🔍 Testing multiple SMTP configurations...")
    
    for server, port in servers_to_test:
        print(f"\n--- Testing {server}:{port} ---")
        
        try:
            print(f"   Connecting to {server}:{port}...")
            smtp = smtplib.SMTP(server, port, timeout=15)
            
            print("   Connected! Getting server info...")
            response = smtp.ehlo()
            print(f"   Server says: {response[1].decode().split()[0]}")
            
            # Check capabilities
            if smtp.has_extn('STARTTLS'):
                print("   ✅ STARTTLS supported")
                smtp.starttls()
                smtp.ehlo()  # Re-identify after STARTTLS
            else:
                print("   ⚠️  STARTTLS not supported")
            
            if smtp.has_extn('AUTH'):
                print("   ✅ AUTH supported")
                auth_methods = smtp.esmtp_features.get('auth', '').split()
                print(f"   Available auth methods: {auth_methods}")
                
                try:
                    smtp.login(username, password)
                    print("   ✅ LOGIN SUCCESSFUL!")
                    smtp.quit()
                    return True
                except Exception as auth_e:
                    print(f"   ❌ Login failed: {auth_e}")
            else:
                print("   ❌ AUTH not supported")
            
            smtp.quit()
            
        except socket.timeout:
            print(f"   ❌ Timeout connecting to {server}:{port}")
        except ConnectionRefusedError:
            print(f"   ❌ Connection refused on {server}:{port}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

def check_dns_mx():
    """Check MX record resolution"""
    print("\n🔍 Checking MX records...")
    try:
        import socket
        mx1 = socket.gethostbyname('mx1.titan.email')
        mx2 = socket.gethostbyname('mx2.titan.email')
        print(f"   mx1.titan.email → {mx1}")
        print(f"   mx2.titan.email → {mx2}")
        return True
    except Exception as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False

if __name__ == "__main__":
    print("📧 Comprehensive Email Configuration Test")
    print("=" * 60)
    
    # Check DNS first
    dns_ok = check_dns_mx()
    
    # Test SMTP
    if dns_ok:
        smtp_ok = test_smtp_detailed()
        
        print("\n" + "=" * 60)
        if smtp_ok:
            print("🎉 SUCCESS: Email system is working!")
        else:
            print("❌ Email authentication failed on all servers")
            print("\n💡 Possible issues:")
            print("   • Email account doesn't exist yet")
            print("   • Password is incorrect")
            print("   • Account needs activation in hosting panel")
            print("   • Different SMTP settings required")
    else:
        print("\n❌ DNS resolution failed - check your internet connection")
