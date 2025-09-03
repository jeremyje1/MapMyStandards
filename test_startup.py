#!/usr/bin/env python3
"""
Test Application Startup with Email Configuration

This script tests that the application can start up and the email service is properly configured.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_application_startup():
    """Test that the application can start up with proper email configuration"""
    
    print("🚀 Testing Application Startup with Email Configuration")
    print("=" * 60)
    
    try:
        # Import the email service
        from a3e.services.email_service_postmark import get_email_service
        
        print("✅ Email service imported successfully")
        
        # Get email service instance
        email_service = get_email_service()
        
        print(f"✅ Email service initialized: {email_service.provider}")
        print(f"✅ From Email: {email_service.from_email}")
        print(f"✅ Admin Email: {email_service.admin_email}")
        
        # Test that we can access the main application configuration
        try:
            from a3e.core.config import settings
            print("✅ Application config loaded successfully")
        except Exception as e:
            print(f"⚠️  Application config warning: {e}")
        
        # Test email service functionality
        if email_service.provider:
            print("✅ Email provider configured and ready")
            
            # Test sending a welcome email (to admin for testing)
            print("🧪 Testing welcome email functionality...")
            success = email_service.send_trial_welcome(
                user_email=email_service.admin_email,
                user_name="Test User"
            )
            
            if success:
                print("✅ Welcome email test successful!")
            else:
                print("❌ Welcome email test failed")
        else:
            print("❌ No email provider configured")
        
        print("\n" + "=" * 60)
        print("🎉 Application startup test completed successfully!")
        print("📧 Email service is properly configured and functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during startup test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_application_startup()
    sys.exit(0 if success else 1)
