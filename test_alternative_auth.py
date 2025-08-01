#!/usr/bin/env python3
"""
Test with alternative password formats and settings
"""

import smtplib

def test_alternative_passwords():
    """Test different password scenarios"""
    
    server = "smtp.titan.email"
    port = 587
    username = "support@mapmystandards.ai"
    
    # Different password scenarios to try
    password_scenarios = [
        ("Current Password", "Ipo4Eva45*"),
        ("Username Only", "support"),
        ("Base64 Encoded", "SXBvNEV2YTQ1Kg=="),  # Base64 of original
        ("Domain\\Username", "mapmystandards.ai\\support")
    ]
    
    print("🔐 Testing Alternative Authentication Methods")
    print("=" * 60)
    
    for scenario_name, test_password in password_scenarios:
        print(f"\n🔍 Testing: {scenario_name}")
        print(f"   Username: {username}")
        print(f"   Password: {'*' * len(test_password)}")
        
        try:
            smtp = smtplib.SMTP(server, port, timeout=15)
            smtp.starttls()
            smtp.ehlo()
            
            smtp.login(username, test_password)
            print("   ✅ SUCCESS!")
            smtp.quit()
            return test_password
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Auth failed: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n❌ All authentication methods failed")
    print(f"\n💡 This confirms you need to:")
    print(f"   1. Contact Namecheap for correct SMTP settings")
    print(f"   2. Check if SMTP needs to be enabled")
    print(f"   3. Get app-specific password if required")
    
    return None

if __name__ == "__main__":
    test_alternative_passwords()
