#!/usr/bin/env python3
"""
Script to add a user to the database with proper password hashing
"""

import os
import sys
import asyncio
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def add_user(email: str, password: str, first_name: str, last_name: str, institution: str):
    """Add a user to the database"""
    
    # Get database URL from environment or use default
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/mapmystandards')
    
    # Convert to async URL if needed
    if DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    elif DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://')
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Check if user exists
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email.lower()}
            )
            existing_user = result.first()
            
            if existing_user:
                # Update existing user
                await session.execute(
                    text("""
                        UPDATE users 
                        SET password_hash = :password_hash,
                            first_name = :first_name,
                            last_name = :last_name,
                            institution = :institution,
                            updated_at = NOW()
                        WHERE email = :email
                    """),
                    {
                        "email": email.lower(),
                        "password_hash": password_hash,
                        "first_name": first_name,
                        "last_name": last_name,
                        "institution": institution
                    }
                )
                print(f"✅ Updated existing user: {email}")
            else:
                # Insert new user
                await session.execute(
                    text("""
                        INSERT INTO users (
                            email, password_hash, first_name, last_name, 
                            institution, subscription_tier, is_trial, 
                            trial_end_date, created_at, updated_at
                        ) VALUES (
                            :email, :password_hash, :first_name, :last_name,
                            :institution, 'trial', true, 
                            :trial_end_date, NOW(), NOW()
                        )
                    """),
                    {
                        "email": email.lower(),
                        "password_hash": password_hash,
                        "first_name": first_name,
                        "last_name": last_name,
                        "institution": institution,
                        "trial_end_date": datetime.now() + timedelta(days=7)
                    }
                )
                print(f"✅ Created new user: {email}")
            
            await session.commit()
            print(f"✅ User {email} is ready to login with the provided password")
            
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

async def main():
    """Main function to add specific users"""
    
    # Add Jeremy's account
    await add_user(
        email="jeremy.estrella@gmail.com",
        password="Ipo4Eva45*",
        first_name="Jeremy",
        last_name="Estrella",
        institution="HCC"
    )
    
    # Add customer account
    await add_user(
        email="jeremy.estrella+cust1@gmail.com",
        password="Ipo4Eva45*",
        first_name="Jeremy",
        last_name="Estrella",
        institution="HCC"
    )

if __name__ == "__main__":
    asyncio.run(main())