#!/usr/bin/env python3
"""
Fix database schema issues for SQLite deployment
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from a3e.models import Base
from a3e.models.user import User
from a3e.core.config import get_settings

async def fix_database():
    """Fix database schema issues"""
    print("🔧 Fixing database schema...")
    
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    
    # Create engine for SQLite
    if settings.database_url.startswith('sqlite'):
        # Fix the User model for SQLite by patching the UUID column
        from sqlalchemy import String
        User.id.type = String(36)  # Change UUID to String for SQLite
        print("✅ Patched User.id column for SQLite compatibility")
    
    # Create engine
    engine = create_engine(
        settings.database_url,
        echo=True if os.getenv('DEBUG') else False
    )
    
    try:
        # Drop and recreate all tables
        print("🗑️  Dropping existing tables...")
        Base.metadata.drop_all(engine)
        
        print("🏗️  Creating new tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Database schema fixed!")
        
        # Test the database
        print("🧪 Testing database...")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Try to query users table
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Users table working - found {count} users")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database())