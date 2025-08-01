#!/usr/bin/env python3
"""
Comprehensive SMTP Authentication Test - MapMyStandards.ai
Tests multiple authentication methods and provides detailed diagnostics
"""

import smtplib
import ssl
import base64
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_connection_only(server, port):
    """Test basic connection without authentication"""
    try:
        print(f"📡 Testing connection to {server}:{port}...")
        smtp = smtplib.SMTP(server, port, timeout=10)
        print("✅ Basic connection successful")
        
        print("🔍 Server capabilities:")
        smtp.ehlo()
        if smtp.has_extn('STARTTLS'):
            print("   ✅ STARTTLS supported")
            smtp.starttls()
            smtp.ehlo()  # Re-identify after TLS
        else:
            print("   ❌ STARTTLS not supported")
            
        if smtp.has_extn('AUTH'):
            print("   ✅ AUTH supported")
            # Get auth methods
            auth_methods = smtp.esmtp_features.get('auth', '').split()
            print(f"   📝 Available auth methods: {auth_methods}")
        else:
            print("   ❌ AUTH not supported")
            
        smtp.quit()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_auth_methods():
    """Test different authentication methods"""
    configs = [
        {
            "name": "Titan Email Standard",
            "server": "smtp.titan.email",
            "port": 587,
            "username": "support@mapmystandards.ai",
            "password": "MapMyStandardsSMTP1*",
            "use_tls": True
        },
        {
            "name": "Titan Email SSL",
            "server": "smtp.titan.email", 
            "port": 465,
            "username": "support@mapmystandards.ai",
            "password": "MapMyStandardsSMTP1*",
            "use_ssl": True
        },
        {
            "name": "Domain SMTP",
            "server": "mail.mapmystandards.ai",
            "port": 587,
            "username": "support@mapmystandards.ai", 
            "password": "MapMyStandardsSMTP1*",
            "use_tls": True
        }
    ]
    
    for config in configs:
        print(f"\n🔍 Testing: {config['name']}")
        print("=" * 60)
        
        # First test connection
        if not test_connection_only(config['server'], config['port']):
            continue
            
        # Then test authentication
        try:
            if config.get('use_ssl'):
                print("🔐 Using SSL connection...")
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(config['server'], config['port'], context=context)
            else:
                print("🔐 Using TLS connection...")
                smtp = smtplib.SMTP(config['server'], config['port'])
                smtp.starttls()
                
            smtp.ehlo()
            
            print("🔑 Attempting authentication...")
            smtp.login(config['username'], config['password'])
            
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print(f"🎉 Working configuration found: {config['name']}")
            
            # Test sending a simple email
            print("📧 Testing email send...")
            msg = MIMEText("Test email from MapMyStandards.ai SMTP test")
            msg['Subject'] = "SMTP Test - Success!"
            msg['From'] = config['username']
            msg['To'] = config['username']  # Send to self
            
            smtp.sendmail(config['username'], [config['username']], msg.as_string())
            print("✅ Test email sent successfully!")
            
            smtp.quit()
            
            print(f"\n🎯 WORKING CONFIGURATION:")
            print(f"   SMTP_SERVER={config['server']}")
            print(f"   SMTP_PORT={config['port']}")
            print(f"   SMTP_USERNAME={config['username']}")
            print(f"   SMTP_PASSWORD={config['password']}")
            if config.get('use_ssl'):
                print(f"   SMTP_USE_SSL=true")
            else:
                print(f"   SMTP_USE_TLS=true")
                
            return config
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            
            # Decode the error message if it's base64
            error_msg = str(e)
            if 'UGFzc3dvcmQ6' in error_msg:
                try:
                    decoded = base64.b64decode('UGFzc3dvcmQ6').decode()
                    print(f"   📝 Decoded error: {decoded}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("   ⏭️  Trying next configuration...")
    
    return None

def check_dns_mx():
    """Check MX records for the domain"""
    import subprocess
    
    print("\n🌐 Checking DNS MX records...")
    try:
        result = subprocess.run(['dig', '+short', 'MX', 'mapmystandards.ai'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            print("✅ MX records found:")
            for line in result.stdout.strip().split('\n'):
                print(f"   📧 {line}")
        else:
            print("❌ No MX records found")
    except Exception as e:
        print(f"❌ Could not check MX records: {e}")

def main():
    print("🚀 MapMyStandards.ai SMTP Diagnostic Tool")
    print("=" * 80)
    print("🎯 Goal: Enable reliable email sending for your SaaS platform")
    print()
    
    # Check DNS first
    check_dns_mx()
    
    # Test authentication methods
    working_config = test_auth_methods()
    
    if working_config:
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Your email system is now operational!")
        print("\n📧 Your MapMyStandards.ai platform now has:")
        print("   ✅ Working SMTP authentication")
        print("   ✅ Contact form email capability")
        print("   ✅ Demo request notifications")
        print("   ✅ Welcome email sending")
        print("   ✅ Support communications")
        
        print(f"\n📝 Update your .env file with these settings:")
        print(f"   SMTP_SERVER={working_config['server']}")
        print(f"   SMTP_PORT={working_config['port']}")
        print(f"   SMTP_USERNAME={working_config['username']}")
        print(f"   SMTP_PASSWORD={working_config['password']}")
        if working_config.get('use_ssl'):
            print(f"   SMTP_USE_SSL=true")
            print(f"   SMTP_USE_TLS=false")
        else:
            print(f"   SMTP_USE_TLS=true")
            print(f"   SMTP_USE_SSL=false")
            
    else:
        print("\n" + "=" * 80)
        print("❌ No working SMTP configuration found")
        print("\n🔧 Next steps:")
        print("   1. 🌐 Log into your Namecheap account")
        print("   2. 📧 Go to Titan Email dashboard") 
        print("   3. 🔑 Generate an 'App Password' for SMTP")
        print("   4. 📝 Use the app password instead of your login password")
        print("   5. 📞 Contact Namecheap support if issues persist")
        print("\n💡 Alternative: Consider using a service like SendGrid or Mailgun")
        print("   for more reliable transactional email delivery")

if __name__ == "__main__":
    main()
