#!/usr/bin/env python3
"""
Migrate the test user we created via API to the database
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

# Import the User model from the correct location
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.a3e.models.user import User

# Test user credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "TestPassword123!"

def hash_password(password: str) -> str:
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

async def migrate_test_user():
    """Create or update test user in database"""
    
    # Database URL
    db_url = "sqlite+aiosqlite:///./a3e_production.db"
    
    # Create engine and session
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        stmt = select(User).where(User.email == TEST_EMAIL)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User {TEST_EMAIL} already exists, updating...")
            # Update existing user
            existing_user.password_hash = hash_password(TEST_PASSWORD)
            existing_user.is_active = True
            existing_user.is_trial = True
            existing_user.trial_end = datetime.utcnow() + timedelta(days=7)
            existing_user.trial_expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            print(f"Creating new user {TEST_EMAIL}...")
            # Create new user
            user = User(
                email=TEST_EMAIL,
                name="Test User",
                first_name="Test",
                last_name="User",
                institution_name="Test Institution",
                password_hash=hash_password(TEST_PASSWORD),
                role="user",
                phone="",
                newsletter_opt_in=False,
                api_key=secrets.token_urlsafe(32),
                plan="professional_monthly",
                billing_period="monthly",
                is_active=True,
                is_trial=True,
                trial_end=datetime.utcnow() + timedelta(days=7),
                trial_expires_at=datetime.utcnow() + timedelta(days=7),
                customer_id=f"cus_{secrets.token_hex(8)}",
                subscription_id=None,
                subscription_tier="trial"
            )
            session.add(user)
        
        await session.commit()
        print(f"✅ User {TEST_EMAIL} is ready in the database!")
        
        # Verify the user
        stmt = select(User).where(User.email == TEST_EMAIL)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User details:")
            print(f"  - ID: {user.id}")
            print(f"  - Email: {user.email}")
            print(f"  - Name: {user.name}")
            print(f"  - Plan: {user.plan}")
            print(f"  - Trial End: {user.trial_end}")
            print(f"  - Is Active: {user.is_active}")
            print(f"  - API Key: {user.api_key[:20]}...")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_test_user())
