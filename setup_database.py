#!/usr/bin/env python3
"""
Database setup script for A3E platform
Creates all necessary tables and initial data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.a3e.models import Base
from src.a3e.models.user import User, UserSession, PasswordReset, UsageEvent
from src.a3e.services.database_service import DatabaseService
from src.a3e.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables"""
    settings = get_settings()
    
    logger.info(f"Connecting to database: {settings.database_url}")
    
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    
    try:
        # Create all tables
        async with db_service.engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully!")
            
        # List all tables created
        async with db_service.engine.connect() as conn:
            from sqlalchemy import inspect
            
            def get_table_names(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(get_table_names)
            logger.info(f"Created tables: {', '.join(tables)}")
            
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        raise
    finally:
        await db_service.engine.dispose()


async def create_test_user():
    """Create a test user account"""
    settings = get_settings()
    
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            # Check if test user already exists
            from sqlalchemy import select
            stmt = select(User).where(User.email == "test@mapmystandards.ai")
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("Test user already exists")
                return
            
            # Create test user
            from datetime import datetime, timedelta
            import bcrypt
            import uuid
            
            test_user = User(
                email="test@mapmystandards.ai",
                name="Test User",
                password_hash=bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode('utf-8'),
                institution_name="Test University",
                institution_type="college",
                role="Accreditation Director",
                is_trial=True,
                trial_started_at=datetime.utcnow(),
                trial_ends_at=datetime.utcnow() + timedelta(days=14),
                subscription_tier="trial",
                api_key=f"test_api_key_{uuid.uuid4().hex[:8]}",
                api_key_created_at=datetime.utcnow()
            )
            
            session.add(test_user)
            await session.commit()
            
            logger.info("✅ Test user created successfully!")
            logger.info(f"   Email: test@mapmystandards.ai")
            logger.info(f"   Password: testpass123")
            logger.info(f"   API Key: {test_user.api_key}")
            
    except Exception as e:
        logger.error(f"❌ Error creating test user: {str(e)}")
        raise
    finally:
        await db_service.engine.dispose()


async def main():
    """Main setup function"""
    logger.info("🚀 Starting A3E database setup...")
    
    # Create tables
    await create_tables()
    
    # Optionally create test user
    if "--with-test-user" in sys.argv:
        await create_test_user()
    
    logger.info("✅ Database setup complete!")


if __name__ == "__main__":
    asyncio.run(main())
