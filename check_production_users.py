#!/usr/bin/env python3
"""Check users in the production database via Railway"""
import os
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    exit(1)

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

print(f"Connecting to: {ASYNC_DATABASE_URL.split('@')[1] if '@' in ASYNC_DATABASE_URL else 'database'}")

async def check_users():
    """Check users in the database"""
    try:
        engine = create_async_engine(ASYNC_DATABASE_URL)
        async with engine.connect() as conn:
            # Check if users table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Users table does not exist!")
                return
                
            print("✅ Users table exists")
            
            # Count users
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"Total users: {user_count}")
            
            # List users (without passwords)
            result = await conn.execute(text("""
                SELECT id, email, name, is_active, is_verified, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """))
            
            users = result.fetchall()
            if users:
                print("\nRecent users:")
                for user in users:
                    print(f"  - {user.email} ({user.name}) - Active: {user.is_active}, Verified: {user.is_verified}")
            else:
                print("\nNo users found in the database")
                
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())