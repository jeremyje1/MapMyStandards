#!/usr/bin/env python3
"""
Test MailerSend with verified domain
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

print("📧 MailerSend SMTP Test - Domain Verification")
print("=" * 60)

# MailerSend settings with your credentials
SMTP_SERVER = "smtp.mailersend.net"
SMTP_PORT = 587
SMTP_USERNAME = "MS_xSQiUP@test-vz9dlemv8qp4kj50.mlsender.net"
SMTP_PASSWORD = "mssp.49hmROn.3zxk54vkj5zljy6v.inVzjZZ"
FROM_EMAIL = "hello@mapmystandards.ai"  # This domain needs to be verified

print(f"🔧 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"📧 From Email: {FROM_EMAIL}")
print(f"👤 Username: {SMTP_USERNAME}")

# Test 1: Try sending to the same domain (should work if mapmystandards.ai is verified)
test_recipients = [
    "info@mapmystandards.ai",  # Same domain as FROM_EMAIL
    "test@mapmystandards.ai",   # Same domain
]

for recipient in test_recipients:
    try:
        print(f"\n🚀 Testing email to {recipient}...")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"MailerSend Domain Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message["From"] = FROM_EMAIL
        message["To"] = recipient
        
        # Create the email content
        text = f"""
Hello!

This is a test email from MapMyStandards using MailerSend SMTP.

Domain verification test for: {FROM_EMAIL}
Recipient: {recipient}
Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
MapMyStandards Team
"""
        
        html = f"""
<html>
  <body>
    <h2>MailerSend Domain Test</h2>
    <p>Hello!</p>
    <p>This is a test email from <strong>MapMyStandards</strong> using MailerSend SMTP.</p>
    <p><strong>Domain verification test for:</strong> {FROM_EMAIL}</p>
    <p><strong>Recipient:</strong> {recipient}</p>
    <p><em>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    <p>Best regards,<br>MapMyStandards Team</p>
  </body>
</html>
"""
        
        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        
        # Add HTML/plain-text parts to MIMEMultipart message
        message.attach(part1)
        message.attach(part2)
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, recipient, message.as_string())
        
        print(f"✅ EMAIL SENT SUCCESSFULLY to {recipient}!")
        break  # If successful, we found a working configuration
        
    except Exception as e:
        print(f"❌ Failed to send to {recipient}: {e}")

print("\n" + "=" * 60)
print("📋 DOMAIN VERIFICATION ANALYSIS")
print("=" * 60)

print("💡 MailerSend requires domain verification for sending emails.")
print("📝 Next steps:")
print("1. Verify 'mapmystandards.ai' domain in MailerSend dashboard")
print("2. Or add 'northpathstrategies.org' as a verified domain")
print("3. Update DNS records as required by MailerSend")
print("4. Once verified, emails will send successfully")

print("\n🔗 MailerSend Dashboard: https://app.mailersend.com/domains")
print("📧 Current FROM domain: mapmystandards.ai (needs verification)")
print("📧 Admin email domain: northpathstrategies.org (needs verification)")

print("\n" + "=" * 60)
