#!/usr/bin/env python3
"""
Script to check the Railway PostgreSQL database schema
"""
import os
import asyncpg
import asyncio
import sys

async def check_database_schema():
    """Check what tables exist in the Railway database"""
    try:
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found")
            return
            
        print(f"Connecting to database...")
        print(f"Database URL (masked): {database_url[:20]}...{database_url[-20:]}")
        
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # List all tables
        print("\n=== TABLES IN DATABASE ===")
        tables = await conn.fetch("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        if not tables:
            print("No tables found in the public schema")
        else:
            for table in tables:
                print(f"  {table['table_name']} ({table['table_type']})")
        
        # Check if users table exists and get its schema
        users_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        if users_exists:
            print("\n=== USERS TABLE SCHEMA ===")
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
                
            # Count users in table
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users;")
            print(f"\n  Total users in table: {user_count}")
            
            if user_count > 0:
                print("\n=== SAMPLE USERS (first 3) ===")
                sample_users = await conn.fetch("SELECT id, email, name, created_at FROM users LIMIT 3;")
                for user in sample_users:
                    print(f"  ID: {user['id']}, Email: {user['email']}, Name: {user['name']}, Created: {user['created_at']}")
        else:
            print("\nNo 'users' table found in database")
            
        # Check for institutions table too
        institutions_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'institutions'
            );
        """)
        
        if institutions_exists:
            print("\n=== INSTITUTIONS TABLE EXISTS ===")
            inst_count = await conn.fetchval("SELECT COUNT(*) FROM institutions;")
            print(f"  Total institutions: {inst_count}")
        else:
            print("\nNo 'institutions' table found")
            
        await conn.close()
        print("\n✅ Database schema check completed")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_schema())