#!/usr/bin/env python3
"""
Test multiple SMTP configurations for Titan Email
"""

import smtplib
import time

def test_smtp_config(server, port, username, password, security_type="STARTTLS"):
    """Test a specific SMTP configuration"""
    print(f"\n🔍 Testing: {server}:{port} ({security_type})")
    print(f"   Username: {username}")
    
    try:
        if security_type == "SSL":
            # SSL connection
            smtp = smtplib.SMTP_SSL(server, port, timeout=15)
        else:
            # Regular connection with optional STARTTLS
            smtp = smtplib.SMTP(server, port, timeout=15)
            
            if security_type == "STARTTLS":
                print("   Starting TLS...")
                smtp.starttls()
        
        smtp.ehlo()
        
        # Check capabilities
        if smtp.has_extn('AUTH'):
            print("   ✅ AUTH supported")
            auth_methods = smtp.esmtp_features.get('auth', '').split()
            print(f"   Auth methods: {auth_methods}")
        else:
            print("   ❌ AUTH not supported")
            smtp.quit()
            return False
        
        # Try authentication
        print("   Attempting login...")
        smtp.login(username, password)
        print("   ✅ LOGIN SUCCESSFUL!")
        
        smtp.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Auth failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_all_configurations():
    """Test all possible SMTP configurations"""
    
    username = "support@mapmystandards.ai"
    password = "Ipo4Eva45*"
    
    # Different configurations to try
    configs = [
        ("smtp.titan.email", 587, "STARTTLS"),
        ("smtp.titan.email", 465, "SSL"),
        ("mail.mapmystandards.ai", 587, "STARTTLS"),
        ("mail.mapmystandards.ai", 465, "SSL"),
        ("smtp.mapmystandards.ai", 587, "STARTTLS"),
        ("outbound.titan.email", 587, "STARTTLS"),
        ("mx1.titan.email", 587, "STARTTLS"),
        ("mx2.titan.email", 587, "STARTTLS")
    ]
    
    print("📧 Testing All Titan Email SMTP Configurations")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    working_configs = []
    
    for server, port, security in configs:
        success = test_smtp_config(server, port, username, password, security)
        if success:
            working_configs.append((server, port, security))
        
        # Small delay between tests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📋 RESULTS SUMMARY")
    print("=" * 60)
    
    if working_configs:
        print("🎉 WORKING CONFIGURATIONS FOUND:")
        for i, (server, port, security) in enumerate(working_configs, 1):
            print(f"\n{i}. Configuration {i}:")
            print(f"   SMTP_SERVER={server}")
            print(f"   SMTP_PORT={port}")
            print(f"   SMTP_USE_TLS={'true' if security == 'STARTTLS' else 'false'}")
            print(f"   SMTP_USE_SSL={'true' if security == 'SSL' else 'false'}")
            print(f"   SMTP_USERNAME={username}")
            print(f"   SMTP_PASSWORD={password}")
        
        print(f"\n🎯 RECOMMENDED: Use Configuration 1")
        print("   Copy these settings to your .env file!")
        
    else:
        print("❌ NO WORKING CONFIGURATIONS FOUND")
        print("\n💡 NEXT STEPS:")
        print("1. Contact Namecheap live chat for exact SMTP settings")
        print("2. Check if account needs additional activation")
        print("3. Verify password is correct in webmail")
        print("4. Ask if app-specific password is required")
    
    return working_configs

if __name__ == "__main__":
    working_configs = test_all_configurations()
    
    if working_configs:
        print(f"\n🚀 Ready to update your email service with working settings!")
    else:
        print(f"\n📞 Contact Namecheap support: https://www.namecheap.com/help-center/live-chat/")
