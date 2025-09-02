#!/usr/bin/env python3
"""
Database migration script to update the schema for proper user authentication
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from src.a3e.database.models import Base
from src.a3e.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Create or update database schema"""
    settings = get_settings()
    
    # Convert sync database URL to async if needed
    db_url = settings.database_url
    if db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    logger.info(f"Connecting to database: {db_url}")
    
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        # Create all tables
        logger.info("Creating database schema...")
        await conn.run_sync(Base.metadata.create_all)
        
        # Add any custom migrations here
        logger.info("Running custom migrations...")
        
        # Check if we need to add missing columns to existing users table
        try:
            # Add columns that might be missing
            migrations = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_name VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR UNIQUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT TRUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR DEFAULT 'professional_monthly'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_period VARCHAR DEFAULT 'monthly'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS customer_id VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_id VARCHAR",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end TIMESTAMP"
            ]
            
            for migration in migrations:
                try:
                    await conn.execute(text(migration))
                    logger.info(f"Executed: {migration}")
                except Exception as e:
                    # Ignore errors for SQLite or if column already exists
                    logger.debug(f"Migration skipped: {migration} - {e}")
        
        except Exception as e:
            logger.warning(f"Custom migrations skipped: {e}")
    
    logger.info("Database migration completed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_database())
