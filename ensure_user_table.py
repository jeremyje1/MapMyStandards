#!/usr/bin/env python3
"""
Ensure User table exists in the database
Run this on Railway after deployment
"""
import os
from sqlalchemy import create_engine, inspect
from src.a3e.models.user import User
from src.a3e.models.database_schema import Base

def ensure_user_table():
    """Create User table if it doesn't exist"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
        
    print(f"📊 Connecting to database...")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Check if user table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'users' in tables:
        print("✅ User table already exists")
        # Check columns
        columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"   Columns: {', '.join(columns)}")
        
        # Check if we need to add onboarding columns
        required_columns = ['institution_name', 'institution_type', 'primary_accreditor', 'onboarding_completed', 'onboarding_data']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"⚠️  Missing columns: {', '.join(missing)}")
            print("   You may need to run a migration")
    else:
        print("🔨 Creating User table...")
        Base.metadata.create_all(bind=engine, tables=[User.__table__])
        print("✅ User table created successfully")
        
    return True

if __name__ == "__main__":
    print("🚀 Ensuring User table exists in database\n")
    
    if ensure_user_table():
        print("\n✨ Database is ready for user settings!")
        print("\nOnboarding data will now persist across sessions.")
    else:
        print("\n❌ Failed to setup database")
        print("Make sure DATABASE_URL is set in your environment")