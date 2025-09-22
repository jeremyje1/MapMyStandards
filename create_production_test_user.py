#!/usr/bin/env python3
"""Create a test user in the production database"""
import asyncio
import os
import bcrypt
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Test user details
TEST_USER = {
    "email": "test@mapmystandards.ai",
    "password": "TestPassword123!",
    "name": "Test User"
}

async def create_test_user():
    """Create a test user in the production database"""
    # Get DATABASE_URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        print("Run this script with: railway run python create_production_test_user.py")
        return
    
    # Convert to async URL
    if DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        ASYNC_DATABASE_URL = DATABASE_URL
    
    print(f"Connecting to database...")
    
    try:
        engine = create_async_engine(ASYNC_DATABASE_URL)
        async with engine.connect() as conn:
            # Generate password hash
            password_hash = bcrypt.hashpw(
                TEST_USER["password"].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Check if user already exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": TEST_USER["email"]}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"User {TEST_USER['email']} already exists, updating password...")
                # Update existing user
                await conn.execute(
                    text("""
                        UPDATE users 
                        SET password_hash = :password_hash,
                            is_active = true,
                            is_verified = true
                        WHERE email = :email
                    """),
                    {
                        "email": TEST_USER["email"],
                        "password_hash": password_hash
                    }
                )
            else:
                print(f"Creating new user {TEST_USER['email']}...")
                # Create new user
                user_id = str(uuid.uuid4())
                await conn.execute(
                    text("""
                        INSERT INTO users (
                            id, email, password_hash, name,
                            is_active, is_verified, created_at,
                            institution_name, role, subscription_tier,
                            trial_ends_at
                        ) VALUES (
                            :id, :email, :password_hash, :name,
                            true, true, :created_at,
                            'Test Institution', 'admin', 'premium',
                            :trial_ends_at
                        )
                    """),
                    {
                        "id": user_id,
                        "email": TEST_USER["email"],
                        "password_hash": password_hash,
                        "name": TEST_USER["name"],
                        "created_at": datetime.utcnow(),
                        "trial_ends_at": datetime.utcnow().replace(year=datetime.utcnow().year + 1)
                    }
                )
            
            await conn.commit()
            print(f"✅ Test user created/updated successfully!")
            print(f"📧 Email: {TEST_USER['email']}")
            print(f"🔑 Password: {TEST_USER['password']}")
            print(f"🌐 Login URL: https://platform.mapmystandards.ai/login")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_user())