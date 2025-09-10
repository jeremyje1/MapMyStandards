#!/usr/bin/env python3
"""Check if jeremy.estrella@gmail.com exists in the database"""

import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.a3e.models.user import User

async def check_user():
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost/a3e_db')
    
    # If it starts with postgres://, replace with postgresql+asyncpg://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    
    print(f"Connecting to database...")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Check for user
            result = await session.execute(
                select(User).where(User.email == 'jeremy.estrella@gmail.com')
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"\n✅ User found!")
                print(f"Email: {user.email}")
                print(f"Name: {user.name}")
                print(f"Password Hash: {'SET' if user.password_hash and user.password_hash != 'pending_reset' else 'PENDING'}")
                print(f"Stripe Customer ID: {user.stripe_customer_id}")
                print(f"Stripe Subscription ID: {user.stripe_subscription_id}")
                print(f"Is Active: {user.is_active}")
                print(f"Is Verified: {user.is_verified}")
                print(f"Created At: {user.created_at}")
            else:
                print("\n❌ User not found in database")
                
            # Check all users count
            result = await session.execute(select(User))
            all_users = result.scalars().all()
            print(f"\nTotal users in database: {len(all_users)}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_user())
