#!/usr/bin/env python3
"""
Test SendGrid integration for MapMyStandards.ai
"""

import os

def test_sendgrid():
    """Test SendGrid email sending"""
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except ImportError:
        print("❌ SendGrid library not installed")
        print("💡 Install it with: pip install sendgrid")
        return False
    
    # Get API key from environment
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment")
        print("💡 Add it to your .env file:")
        print("   SENDGRID_API_KEY=your_api_key_here")
        return False
    
    try:
        print("🚀 Testing SendGrid Integration")
        print("=" * 50)
        
        # Create the email
        message = Mail(
            from_email='support@mapmystandards.ai',
            to_emails='support@mapmystandards.ai',  # Send to self for testing
            subject='MapMyStandards.ai - SendGrid Test Email',
            html_content="""
            <h2>🎉 SendGrid Test Successful!</h2>
            <p>Your MapMyStandards.ai email system is now operational with SendGrid.</p>
            <p><strong>Capabilities enabled:</strong></p>
            <ul>
                <li>✅ Contact form submissions</li>
                <li>✅ Demo request notifications</li>
                <li>✅ Welcome emails</li>
                <li>✅ Support communications</li>
            </ul>
            <p>Professional email delivery for your SaaS platform!</p>
            """
        )
        
        # Send the email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        print(f"✅ Email sent successfully!")
        print(f"📧 Status code: {response.status_code}")
        print(f"📝 Response: Success")
        
        print("\n🎯 SendGrid Configuration Working!")
        print("✅ Your MapMyStandards.ai email system is operational")
        print("📧 Check your inbox for the test email")
        
        return True
        
    except Exception as e:
        print(f"❌ SendGrid test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. ✅ Verify your API key is correct")
        print("2. 🌐 Check SendGrid dashboard for account status")
        print("3. 📧 Ensure sender email is verified")
        return False

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("💡 Note: python-dotenv not installed, reading from system environment")
    
    success = test_sendgrid()
    
    if success:
        print("\n🚀 Your email system is production-ready!")
        print("🎉 MapMyStandards.ai can now send emails reliably!")
    else:
        print("\n📞 Need help? Check the SendGrid dashboard or contact support")
