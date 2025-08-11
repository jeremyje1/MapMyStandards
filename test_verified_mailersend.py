#!/usr/bin/env python3
"""
Test MailerSend with verified mapmystandards.ai domain
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

print("📧 MailerSend SMTP Test - Verified Domain")
print("=" * 60)

# MailerSend settings with verified domain
SMTP_SERVER = "smtp.mailersend.net"
SMTP_PORT = 587
SMTP_USERNAME = "MS_xSQiUP@test-vz9dlemv8qp4kj50.mlsender.net"
SMTP_PASSWORD = "mssp.49hmROn.3zxk54vkj5zljy6v.inVzjZZ"
FROM_EMAIL = "hello@mapmystandards.ai"  # Verified domain
FROM_NAME = "MapMyStandards"

print(f"🔧 SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"📧 From Email: {FROM_EMAIL} (VERIFIED)")
print(f"👤 Username: {SMTP_USERNAME}")

# Test recipients
test_recipients = [
    "info@northpathstrategies.org",  # Admin email
    "test@mapmystandards.ai",        # Same verified domain  
]

success_count = 0
total_tests = len(test_recipients)

for recipient in test_recipients:
    try:
        print(f"\n🚀 Testing email to {recipient}...")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"MapMyStandards Email Test - {datetime.now().strftime('%H:%M:%S')}"
        message["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        message["To"] = recipient
        
        # Create the email content
        text = f"""
Hello!

Great news! The MapMyStandards email system is now working perfectly with MailerSend.

✅ Domain mapmystandards.ai is verified
✅ SMTP credentials are configured
✅ Email delivery is operational

Platform Details:
- From: {FROM_EMAIL}
- To: {recipient}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- System: MapMyStandards SaaS Platform

This confirms that:
✓ Customer notifications will work
✓ Admin alerts will be delivered
✓ System emails are operational

Best regards,
The MapMyStandards Team

---
MapMyStandards - Accreditation Analytics Platform
https://platform.mapmystandards.ai
"""
        
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
      <h1 style="color: white; margin: 0;">MapMyStandards</h1>
      <p style="color: white; margin: 10px 0 0 0;">Email System Test</p>
    </div>
    
    <div style="padding: 30px; background: #f8f9fa;">
      <h2 style="color: #333;">✅ Email System Operational!</h2>
      
      <p>Great news! The MapMyStandards email system is now working perfectly with MailerSend.</p>
      
      <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #28a745; margin-top: 0;">✅ System Status</h3>
        <ul style="list-style: none; padding: 0;">
          <li>✅ Domain mapmystandards.ai is verified</li>
          <li>✅ SMTP credentials are configured</li>
          <li>✅ Email delivery is operational</li>
        </ul>
      </div>
      
      <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
        <strong>Platform Details:</strong><br>
        From: {FROM_EMAIL}<br>
        To: {recipient}<br>
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        System: MapMyStandards SaaS Platform
      </div>
      
      <h3 style="color: #333;">This confirms that:</h3>
      <ul>
        <li>✓ Customer notifications will work</li>
        <li>✓ Admin alerts will be delivered</li>
        <li>✓ System emails are operational</li>
      </ul>
      
      <p>Best regards,<br><strong>The MapMyStandards Team</strong></p>
    </div>
    
    <div style="background: #333; color: white; padding: 15px; text-align: center;">
      <p style="margin: 0;">MapMyStandards - Accreditation Analytics Platform</p>
      <p style="margin: 5px 0 0 0;"><a href="https://platform.mapmystandards.ai" style="color: #64b5f6;">https://platform.mapmystandards.ai</a></p>
    </div>
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
        success_count += 1
        
    except Exception as e:
        print(f"❌ Failed to send to {recipient}: {e}")

print("\n" + "=" * 60)
print("📊 EMAIL TEST RESULTS")
print("=" * 60)

if success_count == total_tests:
    print("🎉 ALL EMAILS SENT SUCCESSFULLY!")
    print("✅ MailerSend integration is fully working")
    print("✅ Domain verification confirmed")
    print("✅ SMTP credentials are correct")
elif success_count > 0:
    print(f"⚠️ PARTIAL SUCCESS: {success_count}/{total_tests} emails sent")
    print("✅ Basic functionality working")
    print("⚠️ Some recipients may need domain verification")
else:
    print("❌ NO EMAILS SENT")
    print("❌ Check domain verification and credentials")

print(f"\n📈 Success Rate: {(success_count/total_tests)*100:.1f}%")
print("📧 Check your inbox for the test emails!")

print("\n💡 Next Steps:")
print("1. Update Railway environment variables with MailerSend credentials")
print("2. Test customer and admin notifications in the platform")
print("3. Verify email functionality in production")

print("\n" + "=" * 60)
