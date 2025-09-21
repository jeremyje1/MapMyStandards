#!/usr/bin/env python3
"""
Check Railway PostgreSQL Database for Users
This script connects to the Railway PostgreSQL database and checks for user records
"""

import os
import asyncio
import asyncpg
from datetime import datetime

async def check_users():
    try:
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            print("ℹ️  To check Railway database, run:")
            print("   railway run python3 check_railway_users.py")
            return
        
        print("🔍 Connecting to Railway PostgreSQL database...")
        print(f"📊 Database URL (masked): {database_url[:20]}...{database_url[-20:]}")
        
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected successfully!")
        
        # Check if users table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        
        if not table_exists:
            print("❌ Users table does not exist!")
            print("ℹ️  This might indicate database migrations haven't been run.")
            
            # Check what tables do exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            if tables:
                print("\n📋 Existing tables:")
                for table in tables:
                    print(f"   - {table['table_name']}")
            else:
                print("\n⚠️  No tables found in database!")
            
            await conn.close()
            return
        
        # Get user count
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"\n👥 Total users in database: {user_count}")
        
        # Get recent users (last 10)
        recent_users = await conn.fetch("""
            SELECT 
                id,
                email,
                name,
                institution_name,
                role,
                created_at,
                is_trial,
                trial_started_at,
                trial_ends_at,
                stripe_customer_id,
                stripe_subscription_id
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        if recent_users:
            print("\n📝 Recent users (last 10):")
            print("-" * 80)
            for user in recent_users:
                print(f"ID: {user['id']}")
                print(f"Email: {user['email']}")
                print(f"Name: {user['name']}")
                print(f"Institution: {user['institution_name']}")
                print(f"Role: {user['role']}")
                print(f"Created: {user['created_at']}")
                print(f"Trial: {user['is_trial']}")
                if user['is_trial']:
                    print(f"Trial Start: {user['trial_started_at']}")
                    print(f"Trial End: {user['trial_ends_at']}")
                print(f"Stripe Customer: {user['stripe_customer_id']}")
                print(f"Stripe Subscription: {user['stripe_subscription_id']}")
                print("-" * 80)
        
        # Check for Houston College specifically
        houston_check = await conn.fetch("""
            SELECT * FROM users 
            WHERE LOWER(institution_name) LIKE '%houston%'
            OR LOWER(email) LIKE '%houston%'
        """)
        
        if houston_check:
            print(f"\n🏫 Found {len(houston_check)} Houston-related users")
            for user in houston_check:
                print(f"   - {user['email']} ({user['institution_name']})")
        else:
            print("\n⚠️  No Houston College users found")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nℹ️  Make sure to run this with Railway environment:")
        print("   railway run python3 check_railway_users.py")

if __name__ == "__main__":
    asyncio.run(check_users())