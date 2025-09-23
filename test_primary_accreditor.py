#!/usr/bin/env python3
"""
Test primary_accreditor and department fields are properly saved/loaded
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from a3e.models.user import User
from a3e.services.user_settings_db import get_user_settings_db

def test_primary_accreditor_fields():
    """Test that primary_accreditor and department fields work correctly"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
        
    print(f"📊 Testing primary_accreditor and department fields...")
    
    # Create test user data
    test_user_info = {
        "sub": "test_accreditor_user",
        "email": "test_accreditor@example.com"
    }
    
    test_settings = {
        "institution_name": "Test University",
        "institution_type": "college",
        "department": "Academic Affairs",
        "role": "Accreditation Director", 
        "primary_accreditor": "WASC",
        "onboarding_completed": True
    }
    
    try:
        # Initialize database service
        db_service = get_user_settings_db()
        
        # Save settings
        print("\n🔨 Saving test user with primary_accreditor and department...")
        if db_service.save_user_settings(test_user_info, test_settings):
            print("✅ Settings saved successfully")
        else:
            print("❌ Failed to save settings")
            return False
            
        # Load settings back
        print("\n📖 Loading settings to verify...")
        loaded_settings = db_service.get_user_settings(test_user_info)
        
        # Verify fields
        success = True
        for field in ["primary_accreditor", "department", "institution_name", "institution_type", "role"]:
            if field in loaded_settings:
                print(f"✅ {field}: {loaded_settings.get(field)}")
            else:
                print(f"❌ {field}: NOT FOUND")
                success = False
                
        # Clean up test user
        print("\n🧹 Cleaning up test user...")
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": "test_accreditor@example.com"})
            conn.commit()
            print("✅ Test user removed")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing primary_accreditor field functionality\n")
    
    if test_primary_accreditor_fields():
        print("\n✨ All tests passed! Primary accreditor field is working correctly.")
    else:
        print("\n❌ Tests failed")