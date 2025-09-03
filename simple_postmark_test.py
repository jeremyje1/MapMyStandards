#!/usr/bin/env python3
"""
Simple Postmark Test

Test sending a simple email via Postmark to validate the configuration.
"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_simple_postmark():
    """Test a simple Postmark email send"""
    try:
        from postmarker.core import PostmarkClient
        
        # Get the token
        token = os.getenv('POSTMARK_SERVER_TOKEN') or os.getenv('POSTMARK_API_TOKEN')
        from_email = os.getenv('FROM_EMAIL', 'info@northpathstrategies.org')
        admin_email = os.getenv('ADMIN_EMAIL', 'info@northpathstrategies.org')
        
        print(f"🧪 Testing Postmark with token: {token[:8]}...{token[-4:]}")
        print(f"From: {from_email}")
        print(f"To: {admin_email}")
        
        # Create client
        client = PostmarkClient(server_token=token)
        
        # Try to send a simple test email
        response = client.emails.send(
            From=from_email,
            To=admin_email,
            Subject="MapMyStandards - Email Configuration Test",
            TextBody="This is a test email to verify that Postmark is configured correctly.",
            HtmlBody="<p>This is a test email to verify that <strong>Postmark</strong> is configured correctly.</p>",
            MessageStream="outbound"
        )
        
        print("✅ Email sent successfully!")
        print(f"Message ID: {response['MessageID']}")
        print(f"Status: {response['ErrorCode']} - {response['Message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        
        # Parse the error for better debugging
        error_str = str(e)
        if "Server token" in error_str:
            print("💡 The server token appears to be invalid")
            print("   Please check your Postmark account settings and verify the token")
        elif "Domain" in error_str:
            print("💡 Domain verification issue")
            print("   Please verify your sending domain in Postmark")
        elif "From" in error_str:
            print("💡 From address issue")
            print("   Please verify your From email address is approved in Postmark")
        
        return False

if __name__ == "__main__":
    print("🚀 Simple Postmark Email Test")
    print("=" * 40)
    test_simple_postmark()
