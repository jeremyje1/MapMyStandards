#!/usr/bin/env python3
"""
Test MailerSend integration specifically
"""
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

print("📧 MailerSend SMTP Test")
print("=" * 60)

# Load MailerSend configuration from env file if it exists
config_files = ['mailersend.env', '.env', 'MAILERSEND_ENV_EXAMPLE.txt']
config = {}

for config_file in config_files:
    if os.path.exists(config_file):
        print(f"📄 Loading config from {config_file}")
        with open(config_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
        break

# MailerSend SMTP settings
SMTP_SERVER = config.get('SMTP_SERVER', 'smtp.mailersend.net')
SMTP_PORT = int(config.get('SMTP_PORT', '587'))
SMTP_USERNAME = config.get('SMTP_USERNAME', '')
SMTP_PASSWORD = config.get('SMTP_PASSWORD', '')
FROM_EMAIL = config.get('FROM_EMAIL', 'hello@mapmystandards.ai')

print(f"🔧 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"📧 From Email: {FROM_EMAIL}")
print(f"👤 Username configured: {'Yes' if SMTP_USERNAME else 'No'}")
print(f"🔐 Password configured: {'Yes' if SMTP_PASSWORD else 'No'}")

if not SMTP_USERNAME or not SMTP_PASSWORD:
    print("❌ Missing SMTP credentials")
    print("💡 Create a .env file with:")
    print("   SMTP_USERNAME=your_mailersend_username")
    print("   SMTP_PASSWORD=your_mailersend_password")
    print("   FROM_EMAIL=hello@mapmystandards.ai")
    exit(1)

try:
    print("\n🚀 Testing SMTP connection...")
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = f"MailerSend Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    message["From"] = FROM_EMAIL
    message["To"] = "info@northpathstrategies.org"
    
    # Create the plain-text and HTML version of your message
    text = f"""
Hello!

This is a test email from MapMyStandards using MailerSend SMTP.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
MapMyStandards Team
"""
    
    html = f"""
<html>
  <body>
    <h2>MailerSend Test Email</h2>
    <p>Hello!</p>
    <p>This is a test email from <strong>MapMyStandards</strong> using MailerSend SMTP.</p>
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
        server.sendmail(FROM_EMAIL, "info@northpathstrategies.org", message.as_string())
    
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print("📧 Email sent to info@northpathstrategies.org")
    print("🎉 MailerSend SMTP integration is working!")

except Exception as e:
    print(f"❌ SMTP Error: {e}")
    print("\n🔍 Troubleshooting steps:")
    print("1. Check your MailerSend credentials")
    print("2. Verify the domain is verified in MailerSend")
    print("3. Check SMTP settings in MailerSend dashboard")

print("\n" + "=" * 60)
print("📋 MAILERSEND TEST COMPLETE")
print("=" * 60)
