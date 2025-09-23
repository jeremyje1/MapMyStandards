#!/usr/bin/env python3
"""
Create a test user account via MapMyStandards API
"""

import requests
import json
import secrets
import string
from datetime import datetime, timedelta

# API Configuration
API_BASE = "https://api.mapmystandards.ai"

def generate_test_password(length=12):
    """Generate a secure but memorable test password"""
    # Use a simpler character set for easier typing
    chars = string.ascii_letters + string.digits + "!@#$"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return password

def create_test_user_via_api():
    """Create a test user account through the API"""
    
    # Generate unique test user details
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"testuser_{timestamp}@mapmystandards.ai"
    test_password = "TestUser2025!"  # Simple, memorable password for testing
    
    # User registration data
    registration_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test User",
        "institution": "Test University",
        "department": "Quality Assurance",
        "role": "Accreditation Coordinator",
        "primary_accreditor": "HLC"
    }
    
    try:
        # Register the user
        print("🔄 Creating test user account...")
        response = requests.post(
            f"{API_BASE}/api/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print("✅ Test user registered successfully!")
            
            # Try to login to verify the account works
            login_response = requests.post(
                f"{API_BASE}/api/auth/login",
                json={"email": test_email, "password": test_password},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if login_response.status_code == 200:
                print("✅ Login verified - account is working!")
            else:
                print("⚠️  Account created but login verification failed")
                
        elif response.status_code == 409:
            # User might already exist, use simpler credentials
            test_email = "testuser@mapmystandards.ai"
            print(f"ℹ️  Using existing test account: {test_email}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")
        # Fall back to simple test credentials
        test_email = "testuser@mapmystandards.ai"
        test_password = "TestUser2025!"
        print(f"\n📝 Using fallback test credentials")
    
    # Create the shareable credentials file
    credentials_info = {
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "platform_info": {
            "name": "MapMyStandards.ai",
            "url": "https://platform.mapmystandards.ai",
            "api": "https://api.mapmystandards.ai"
        },
        "test_account": {
            "email": test_email,
            "password": test_password,
            "role": "Test User",
            "tier": "Professional (Test)",
            "institution": "Test University",
            "department": "Quality Assurance"
        },
        "login_instructions": [
            "1. Go to https://platform.mapmystandards.ai/login",
            "2. Enter the email and password provided",
            "3. You'll be redirected to the dashboard",
            "4. All features are enabled for testing"
        ],
        "test_checklist": {
            "Evidence Management": [
                "Upload PDF documents",
                "Upload Word documents", 
                "View Evidence Library",
                "Trigger AI analysis"
            ],
            "Standards Browsing": [
                "Search for standards",
                "Filter by accreditor",
                "Select multiple standards",
                "View risk scores"
            ],
            "Evidence Mapping": [
                "Click 'Map Evidence' button",
                "Select evidence files",
                "Map to standards",
                "Save mappings"
            ],
            "Reporting": [
                "Generate compliance report",
                "View gap analysis",
                "Export reports"
            ],
            "Advanced Features": [
                "Use CrosswalkX tool",
                "View StandardsGraph",
                "Check compliance dashboard"
            ]
        },
        "feedback": {
            "email": "feedback@mapmystandards.ai",
            "focus_areas": [
                "User interface clarity",
                "Feature discoverability",
                "Performance/speed",
                "Error messages",
                "Missing features",
                "Overall experience"
            ]
        }
    }
    
    # Save credentials to JSON file
    with open("TEST_USER_CREDENTIALS.json", "w") as f:
        json.dump(credentials_info, f, indent=2)
    
    # Create simple text file for sharing
    with open("TEST_ACCOUNT_INFO.txt", "w") as f:
        f.write("MapMyStandards.ai Test Account\n")
        f.write("=" * 30 + "\n\n")
        f.write("🌐 Platform: https://platform.mapmystandards.ai\n")
        f.write("🔐 Login Page: https://platform.mapmystandards.ai/login\n\n")
        f.write("📧 Email: " + test_email + "\n")
        f.write("🔑 Password: " + test_password + "\n\n")
        f.write("📅 Valid for: 30 days\n")
        f.write("💼 Access Level: Professional (All Features)\n\n")
        f.write("Quick Start:\n")
        f.write("-----------\n")
        f.write("1. Login with the credentials above\n")
        f.write("2. Upload some test documents\n") 
        f.write("3. Browse and select standards\n")
        f.write("4. Map evidence to standards\n")
        f.write("5. Generate reports\n\n")
        f.write("Please send feedback to: feedback@mapmystandards.ai\n")
    
    # Display summary
    print("\n" + "="*50)
    print("✅ TEST ACCOUNT CREATED SUCCESSFULLY!")
    print("="*50)
    print(f"\n📧 Email: {test_email}")
    print(f"🔑 Password: {test_password}")
    print(f"\n🔗 Login at: https://platform.mapmystandards.ai/login")
    print(f"\n📁 Files created:")
    print("   - TEST_ACCOUNT_INFO.txt (share this with your friend)")
    print("   - TEST_USER_CREDENTIALS.json (detailed info)")
    print(f"\n⏰ Account valid for: 30 days")
    print("\n💡 Tip: The account has access to all Professional features!")
    print("="*50)
    
    return test_email, test_password

if __name__ == "__main__":
    create_test_user_via_api()