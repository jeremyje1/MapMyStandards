#!/usr/bin/env python3
"""
Email configuration test for MapMyStandards.ai
Tests SMTP connectivity and email sending functionality
"""

import smtplib
import dns.resolver
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sys

def test_mx_records():
    """Test if MX records are properly configured"""
    try:
        mx_records = dns.resolver.resolve('mapmystandards.ai', 'MX')
        print("✅ MX Records found:")
        for mx in mx_records:
            print(f"   Priority {mx.preference}: {mx.exchange}")
        return True
    except Exception as e:
        print(f"❌ MX Record lookup failed: {e}")
        return False

def test_spf_record():
    """Test SPF record configuration"""
    try:
        txt_records = dns.resolver.resolve('mapmystandards.ai', 'TXT')
        spf_found = False
        for txt in txt_records:
            txt_string = str(txt).strip('"')
            if txt_string.startswith('v=spf1'):
                print(f"✅ SPF Record found: {txt_string}")
                spf_found = True
        
        if not spf_found:
            print("❌ No SPF record found")
        return spf_found
    except Exception as e:
        print(f"❌ SPF Record lookup failed: {e}")
        return False

def test_smtp_connection(smtp_server="mx1.titan.email", port=587):
    """Test SMTP connection to Titan Email"""
    try:
        print(f"🔍 Testing SMTP connection to {smtp_server}:{port}")
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()
        
        # Check if STARTTLS is supported
        if server.has_extn('STARTTLS'):
            print("✅ STARTTLS supported")
            server.starttls()
        else:
            print("⚠️  STARTTLS not supported")
        
        server.quit()
        print(f"✅ SMTP connection to {smtp_server} successful")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def send_test_email(from_email, password, to_email, smtp_server="mx1.titan.email", port=587):
    """Send a test email (requires valid credentials)"""
    try:
        # Create message
        msg = MimeMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "MapMyStandards.ai Email Test"
        
        body = """
        This is a test email from your MapMyStandards.ai email system.
        
        If you receive this email, your email configuration is working correctly!
        
        Best regards,
        MapMyStandards.ai System
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Test email sent successfully from {from_email} to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def main():
    print("🔍 MapMyStandards.ai Email Configuration Test")
    print("=" * 50)
    
    # Test DNS configuration
    print("\n1. Testing DNS Configuration:")
    mx_ok = test_mx_records()
    spf_ok = test_spf_record()
    
    # Test SMTP connectivity
    print("\n2. Testing SMTP Connectivity:")
    smtp_ok = test_smtp_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Configuration Summary:")
    print(f"   MX Records: {'✅ OK' if mx_ok else '❌ FAIL'}")
    print(f"   SPF Record: {'✅ OK' if spf_ok else '❌ FAIL'}")
    print(f"   SMTP Connection: {'✅ OK' if smtp_ok else '❌ FAIL'}")
    
    if mx_ok and spf_ok and smtp_ok:
        print("\n🎉 Your email infrastructure is properly configured!")
        print("\nNext steps:")
        print("1. Create email accounts in your Titan Email admin panel")
        print("2. Test sending emails with actual credentials")
        print("3. Update your application's SMTP settings")
    else:
        print("\n⚠️  Some issues found. Please check the failed items above.")
    
    # Optional: Test actual email sending (requires credentials)
    print("\n" + "=" * 50)
    print("To test actual email sending, run:")
    print("python test_email.py send your-email@mapmystandards.ai your-password test-recipient@example.com")

if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "send":
        from_email = sys.argv[2]
        password = sys.argv[3]
        to_email = sys.argv[4]
        send_test_email(from_email, password, to_email)
    else:
        main()
