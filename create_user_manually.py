#!/usr/bin/env python3
"""
Manually create a user in the database since the registration process
is using the wrong auth router (in-memory instead of database)
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import secrets

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from a3e.models.user import User
from a3e.models import Base

async def create_user():
    # Get database URL from Railway
    database_url = input("Enter the DATABASE_URL from Railway (postgres://...): ").strip()
    
    # Convert to async URL
    if database_url.startswith('postgresql://'):
        async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    elif database_url.startswith('postgres://'):
        async_database_url = database_url.replace('postgres://', 'postgresql+asyncpg://')
    else:
        async_database_url = database_url
    
    print(f"Connecting to database...")
    
    # Create engine
    engine = create_async_engine(async_database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        # Check if user already exists
        email = "jeremy.estrella@gmail.com"
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User {email} already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Created at: {existing_user.created_at}")
            return
        
        # Create new user
        user = User(
            email=email,
            name="Jeremy Estrella",
            password_hash="salt:hash",  # You'll need to login via reset password
            institution_name="Test Institution",
            institution_type="college",
            role="Administrator",
            is_trial=True,
            trial_started_at=datetime.utcnow(),
            trial_ends_at=datetime.utcnow() + timedelta(days=7),
            subscription_tier="professional",
            api_key=secrets.token_urlsafe(32),
            api_key_created_at=datetime.utcnow(),
            is_active=True,
            is_verified=True,
            email_verified_at=datetime.utcnow()
        )
        
        session.add(user)
        await session.commit()
        
        print(f"\nUser created successfully!")
        print(f"Email: {user.email}")
        print(f"User ID: {user.id}")
        print(f"API Key: {user.api_key}")
        print(f"Trial ends at: {user.trial_ends_at}")
        print(f"\nIMPORTANT: You'll need to use 'Forgot Password' to set a password")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_user())
