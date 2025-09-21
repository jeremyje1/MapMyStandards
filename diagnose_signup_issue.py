#!/usr/bin/env python3
"""
Diagnose why trial signups are not creating users in the Railway PostgreSQL database
"""

import requests
import json
from datetime import datetime

# API endpoints
API_BASE = "https://api.mapmystandards.ai"

def test_trial_signup():
    """Test the trial signup endpoint to see if users are created"""
    
    print("🔍 Testing Trial Signup Process")
    print("=" * 50)
    
    # Generate unique test data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_data = {
        "name": f"Test User {timestamp}",
        "institution_name": f"Test College {timestamp}",
        "institution_type": "university",
        "email": f"test_{timestamp}@example.com",
        "password": "TestPassword123!",
        "role": "Accreditation Director",
        "plan": "college_monthly",
        "phone": "555-0123",
        "newsletter_opt_in": False,
        "payment_method_id": "pm_card_visa"  # Test payment method
    }
    
    print(f"📧 Test Email: {test_data['email']}")
    print(f"🏫 Institution: {test_data['institution_name']}")
    
    try:
        # Test the /api/trial/signup endpoint
        print("\n1️⃣ Testing /api/trial/signup endpoint...")
        response = requests.post(
            f"{API_BASE}/api/trial/signup",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {json.dumps(result, indent=2)}")
            
            if result.get('api_key'):
                print(f"\n   🔑 API Key generated: {result['api_key'][:20]}...")
                return result['api_key']
        else:
            print(f"   ❌ Error: {response.text}")
            
            # Try parsing error details
            try:
                error_detail = response.json()
                print(f"   Error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
                
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    return None

def check_user_exists(api_key):
    """Check if the user was actually created by trying to use their API key"""
    
    print("\n2️⃣ Verifying user creation with API key...")
    
    try:
        # Try to access a protected endpoint with the API key
        response = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/dashboard/metrics",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ User successfully created and can access protected endpoints!")
            return True
        elif response.status_code == 401:
            print("   ❌ User creation may have failed - API key is invalid")
            return False
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking user: {e}")
        return False

def check_database_directly():
    """Provide instructions for checking the database directly"""
    
    print("\n3️⃣ To check the Railway database directly:")
    print("   Run: railway run python3 check_railway_users.py")
    print("   This will show all users in the database")
    
    print("\n4️⃣ To check Railway logs for errors:")
    print("   Run: railway logs")
    print("   Look for any database connection or user creation errors")

def main():
    """Main diagnostic flow"""
    
    print("\n🏥 MapMyStandards Signup Diagnostic Tool")
    print("This will help identify why users aren't being created in the database")
    print("\n")
    
    # Test signup
    api_key = test_trial_signup()
    
    if api_key:
        # Verify the user was created
        user_exists = check_user_exists(api_key)
        
        if user_exists:
            print("\n✅ DIAGNOSIS: Signup is working correctly!")
            print("   The user was created and can access the platform.")
        else:
            print("\n❌ DIAGNOSIS: Signup endpoint returns success but user not accessible")
            print("   Possible issues:")
            print("   - Database write failed silently")
            print("   - API key generation issue")
            print("   - Authentication service misconfiguration")
    else:
        print("\n❌ DIAGNOSIS: Signup endpoint is failing")
        print("   Possible issues:")
        print("   - Database connection problem")
        print("   - Stripe integration issue")
        print("   - Server configuration error")
    
    # Provide next steps
    check_database_directly()
    
    print("\n5️⃣ Common issues to check:")
    print("   - DATABASE_URL environment variable in Railway")
    print("   - Database migrations (alembic upgrade head)")
    print("   - Stripe webhook configuration")
    print("   - CORS settings for frontend domain")

if __name__ == "__main__":
    main()