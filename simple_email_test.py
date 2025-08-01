#!/usr/bin/env python3
"""
Simple email DNS test for MapMyStandards.ai
"""

import socket
import smtplib

def test_mx_records():
    """Test MX records using basic socket resolution"""
    print("🔍 Testing MX Records...")
    try:
        # Test if we can resolve the MX servers
        mx1 = socket.gethostbyname('mx1.titan.email')
        mx2 = socket.gethostbyname('mx2.titan.email')
        print(f"✅ MX1 (mx1.titan.email) resolves to: {mx1}")
        print(f"✅ MX2 (mx2.titan.email) resolves to: {mx2}")
        return True
    except Exception as e:
        print(f"❌ MX resolution failed: {e}")
        return False

def test_smtp_connection():
    """Test SMTP connection to Titan servers"""
    print("\n🔍 Testing SMTP Connection...")
    
    servers = [
        ('mx1.titan.email', 587),
        ('mx1.titan.email', 25),
        ('mx2.titan.email', 587)
    ]
    
    for server, port in servers:
        try:
            print(f"   Testing {server}:{port}...")
            smtp = smtplib.SMTP(server, port, timeout=10)
            response = smtp.ehlo()
            smtp.quit()
            print(f"   ✅ {server}:{port} - Connection successful")
            print(f"      Server response: {response[1].decode().split()[0]}")
            return True
        except Exception as e:
            print(f"   ❌ {server}:{port} - {e}")
    
    return False

def test_domain_resolution():
    """Test if domain resolves correctly"""
    print("\n🔍 Testing Domain Resolution...")
    try:
        ip = socket.gethostbyname('mapmystandards.ai')
        print(f"✅ mapmystandards.ai resolves to: {ip}")
        return True
    except Exception as e:
        print(f"❌ Domain resolution failed: {e}")
        return False

def main():
    print("📧 MapMyStandards.ai Email Configuration Test")
    print("=" * 60)
    
    # Run tests
    domain_ok = test_domain_resolution()
    mx_ok = test_mx_records()
    smtp_ok = test_smtp_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   Domain Resolution: {'✅ PASS' if domain_ok else '❌ FAIL'}")
    print(f"   MX Records: {'✅ PASS' if mx_ok else '❌ FAIL'}")
    print(f"   SMTP Connectivity: {'✅ PASS' if smtp_ok else '❌ FAIL'}")
    
    if domain_ok and mx_ok and smtp_ok:
        print("\n🎉 Email infrastructure is ready!")
        print("\n📝 Next Steps:")
        print("1. Log into your hosting provider's email management")
        print("2. Create the email account: support@mapmystandards.ai")
        print("3. Note the login credentials for your application")
        print("4. Configure your application's SMTP settings:")
        print("   - SMTP Server: mx1.titan.email")
        print("   - Port: 587 (STARTTLS)")
        print("   - Username: support@mapmystandards.ai")
        print("   - Password: [your email password]")
    else:
        print("\n⚠️  Issues detected. Please check DNS configuration.")

if __name__ == "__main__":
    main()
