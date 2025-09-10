#!/usr/bin/env python3
"""Test Railway PostgreSQL database connection and user table"""

import asyncio
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Railway DATABASE_URL
DATABASE_URL = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@postgres-rlai.railway.internal:5432/railway"

# Convert to asyncpg URL format
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def test_database():
    print("🔍 Testing Railway PostgreSQL Database Connection")
    print("=" * 50)
    print(f"Database: postgres-rlai.railway.internal")
    print(f"Database name: railway")
    
    try:
        # Create async engine
        engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Test basic connection
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n✅ Connected successfully!")
            print(f"PostgreSQL version: {version}")
            
            # Check if users table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print(f"\n✅ 'users' table exists")
                
                # Count users
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"Total users: {user_count}")
                
                # Check for recent users
                result = await session.execute(text("""
                    SELECT email, created_at, stripe_customer_id, is_trial
                    FROM users 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                recent_users = result.fetchall()
                
                if recent_users:
                    print("\n📋 Recent users:")
                    for user in recent_users:
                        print(f"  - {user.email} (created: {user.created_at}, trial: {user.is_trial})")
                else:
                    print("\n⚠️  No users found in database")
                    
                # Check for jeremy.estrella@gmail.com
                result = await session.execute(text("""
                    SELECT email, stripe_customer_id, stripe_subscription_id, created_at
                    FROM users 
                    WHERE email = 'jeremy.estrella@gmail.com'
                """))
                jeremy = result.fetchone()
                
                if jeremy:
                    print(f"\n✅ Found jeremy.estrella@gmail.com:")
                    print(f"   Customer ID: {jeremy.stripe_customer_id}")
                    print(f"   Subscription ID: {jeremy.stripe_subscription_id}")
                    print(f"   Created: {jeremy.created_at}")
                else:
                    print(f"\n❌ jeremy.estrella@gmail.com not found in database")
                
            else:
                print(f"\n❌ 'users' table does NOT exist!")
                print("The database might not be initialized properly.")
                
                # List all tables
                result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
                tables = result.fetchall()
                
                if tables:
                    print("\nAvailable tables:")
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print("\n⚠️  No tables found. Database appears to be empty.")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"Error: {type(e).__name__}: {e}")
        
        # Try external connection URL for testing
        print("\n🔧 Note: The internal URL only works from within Railway.")
        print("For external testing, use Railway's proxy or port forwarding.")

if __name__ == "__main__":
    print("Note: This script uses Railway's internal database URL.")
    print("It will only work when run from within the Railway environment.\n")
    asyncio.run(test_database())
