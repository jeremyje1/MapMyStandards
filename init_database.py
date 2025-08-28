#!/usr/bin/env python3
"""
Initialize database on Railway startup
"""
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        from sqlalchemy import create_engine, inspect
        from a3e.models import Base
        from a3e.core.config import get_settings
        
        print("🚀 Initializing database...")
        
        settings = get_settings()
        
        # Create engine
        engine = create_engine(settings.database_url)
        
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'users' not in existing_tables:
            print("📋 Creating database tables...")
            Base.metadata.create_all(engine)
            print("✅ Database tables created successfully")
        else:
            print("✅ Database tables already exist")
            
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't fail the startup - app should still run
        pass

if __name__ == "__main__":
    init_database()