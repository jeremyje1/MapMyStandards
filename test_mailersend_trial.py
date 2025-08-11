#!/usr/bin/env python3
"""
Test MailerSend trial account limitations
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

print("📧 MailerSend Trial Account Test")
print("=" * 60)

# MailerSend settings
SMTP_SERVER = "smtp.mailersend.net"
SMTP_PORT = 587
SMTP_USERNAME = "MS_xSQiUP@test-vz9dlemv8qp4kj50.mlsender.net"
SMTP_PASSWORD = "mssp.49hmROn.3zxk54vkj5zljy6v.inVzjZZ"
FROM_EMAIL = "hello@mapmystandards.ai"
FROM_NAME = "MapMyStandards"

print(f"🔧 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"📧 From Email: {FROM_EMAIL}")
print(f"👤 Username: {SMTP_USERNAME}")

# Trial accounts can only send to admin email
# Let's try the email associated with the MailerSend account
possible_admin_emails = [
    "jeremy@northpathstrategies.org",
    "admin@mapmystandards.ai",
    "hello@mapmystandards.ai",
    # The username suggests the admin email might be related to the account
]

print("\n💡 MailerSend Trial Account Limitations:")
print("- Trial accounts can only send to administrator's email")
print("- Need to find the correct admin email for this account")
print("- Once upgraded, can send to any verified domain")

for admin_email in possible_admin_emails:
    try:
        print(f"\n🚀 Testing with potential admin email: {admin_email}")
        
        # Create simple message
        message = MIMEText(f"""
MailerSend Trial Test

This is a test to find the correct administrator email for the MailerSend trial account.

If you receive this email, then {admin_email} is the admin email for this account.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MapMyStandards Team
""")
        
        message["Subject"] = f"MailerSend Trial Test - {datetime.now().strftime('%H:%M')}"
        message["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        message["To"] = admin_email
        
        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, admin_email, message.as_string())
        
        print(f"✅ SUCCESS! Email sent to {admin_email}")
        print(f"🎯 Found admin email: {admin_email}")
        
        # Update the configuration
        print(f"\n📝 Update your configuration:")
        print(f"ADMIN_EMAIL={admin_email}")
        break
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        if "Trial accounts can only send emails to the administrator's email" not in str(e):
            print(f"   (Different error - might indicate wrong admin email)")

print("\n" + "=" * 60)
print("📋 TRIAL ACCOUNT SOLUTION")
print("=" * 60)

print("🔍 Current Status: MailerSend Trial Account")
print("\n📧 Trial Account Limitations:")
print("- Can only send emails to the account administrator")
print("- Recipient domains must be verified")
print("- Limited sending volume")

print("\n🚀 Solutions:")
print("1. Find the correct admin email (testing above)")
print("2. Upgrade MailerSend account to remove restrictions")
print("3. Verify additional domains in MailerSend dashboard")

print("\n💡 For Production:")
print("- Consider upgrading MailerSend account")
print("- Verify both mapmystandards.ai and northpathstrategies.org")
print("- This will allow full customer email functionality")

print("\n🔗 MailerSend Dashboard: https://app.mailersend.com/")
print("\n" + "=" * 60)
