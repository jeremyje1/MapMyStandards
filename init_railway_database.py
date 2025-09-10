#!/usr/bin/env python3
"""Initialize Railway PostgreSQL database with required tables"""

import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Railway DATABASE_URL (internal)
DATABASE_URL = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@postgres-rlai.railway.internal:5432/railway"
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def init_database():
    print("🔧 Initializing Railway PostgreSQL Database")
    print("=" * 50)
    
    try:
        # Create engine
        engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
        
        # Import models to register them
        from a3e.models import Base
        from a3e.models.user import User, PasswordReset
        from a3e.models.trial_request import TrialRequest
        from a3e.models.subscription import Subscription
        
        print("\n📋 Creating tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ Database initialized successfully!")
        
        # Verify tables were created
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            print("\n📋 Created tables:")
            for table in tables:
                print(f"  ✅ {table[0]}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ Database initialization failed!")
        print(f"Error: {type(e).__name__}: {e}")
        
        if "railway.internal" in str(e):
            print("\n⚠️  This script must be run from within Railway environment.")
            print("Options:")
            print("1. Run via Railway CLI: railway run python init_railway_database.py")
            print("2. Deploy and run in production")

if __name__ == "__main__":
    asyncio.run(init_database())
