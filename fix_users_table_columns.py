#!/usr/bin/env python3
"""Fix missing columns in users table"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get DATABASE_URL from environment or use the Railway URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@postgres-rlai.railway.internal:5432/railway')

# Convert to asyncpg URL format
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def add_missing_columns():
    print("🔧 Adding missing columns to users table")
    print("=" * 50)
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Check which columns exist
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
        """))
        existing_columns = {row[0] for row in result}
        
        print(f"\nFound {len(existing_columns)} existing columns")
        
        # Add missing columns
        columns_to_add = [
            ("onboarding_completed", "BOOLEAN DEFAULT FALSE"),
            ("onboarding_data", "JSONB DEFAULT '{}'::jsonb"),
            ("documents_analyzed", "INTEGER DEFAULT 0"),
            ("reports_generated", "INTEGER DEFAULT 0"),
            ("compliance_checks_run", "INTEGER DEFAULT 0"),
            ("newsletter_opt_in", "BOOLEAN DEFAULT TRUE"),
            ("phone", "VARCHAR"),
            ("reset_token", "VARCHAR"),
            ("reset_token_expires", "TIMESTAMP"),
            ("refresh_token", "VARCHAR"),
            ("refresh_token_expires", "TIMESTAMP"),
            ("last_login", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("email_verified_at", "TIMESTAMP"),
            ("api_key_created_at", "TIMESTAMP"),
            ("first_name", "VARCHAR"),
            ("last_name", "VARCHAR")
        ]
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                try:
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"❌ Failed to add {column_name}: {e}")
            else:
                print(f"⏭️  Column already exists: {column_name}")
        
        # Create indexes for performance
        print("\n📊 Creating indexes...")
        indexes = [
            ("idx_users_email", "users(email)"),
            ("idx_users_stripe_customer_id", "users(stripe_customer_id)"),
            ("idx_users_created_at", "users(created_at)")
        ]
        
        for index_name, index_def in indexes:
            try:
                await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}"))
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️  Index issue: {e}")
        
        print("\n✅ Database schema updated successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_missing_columns())
