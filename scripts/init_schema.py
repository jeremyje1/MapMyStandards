#!/usr/bin/env python3
"""
Database Schema Management

Creates tables from SQLAlchemy models if they don't exist.
Provides basic schema initialization without full Alembic migrations.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from src.a3e.core.config import get_settings
from src.a3e.services.database_service import DatabaseService
from src.a3e.models import Base

logger = logging.getLogger(__name__)


async def create_schema():
    """Create database schema from models"""
    settings = get_settings()
    db_service = DatabaseService(settings.database_url)
    
    try:
        await db_service.initialize()
        logger.info("Database connection established")
        
        # Create all tables from Base metadata
        async with db_service.engine.begin() as conn:
            # Check if any tables exist
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table';" if 
                settings.database_url.startswith('sqlite') else
                "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            ))
            existing_tables = [row[0] for row in result.fetchall()]
            
            if existing_tables:
                logger.info(f"Found {len(existing_tables)} existing tables: {existing_tables}")
            else:
                logger.info("No existing tables found - creating schema")
                
            # Create tables that don't exist
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Schema creation completed")
            
        await db_service.close()
        
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        raise


async def check_schema():
    """Check current schema status"""
    settings = get_settings()
    db_service = DatabaseService(settings.database_url)
    
    try:
        await db_service.initialize()
        
        async with db_service.engine.begin() as conn:
            # Get table info
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table';" if
                settings.database_url.startswith('sqlite') else
                "SELECT tablename FROM pg_tables WHERE schemaname='public';"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Database: {settings.database_url}")
            print(f"Tables ({len(tables)}): {', '.join(sorted(tables)) if tables else 'None'}")
            
            # Check if core A3E tables exist
            core_tables = ['institutions', 'accreditors', 'standards', 'evidence', 'agent_workflows']
            missing = [t for t in core_tables if t not in tables]
            if missing:
                print(f"Missing core tables: {missing}")
                return False
            else:
                print("✅ All core tables present")
                return True
                
        await db_service.close()
        
    except Exception as e:
        print(f"Schema check failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        asyncio.run(check_schema())
    else:
        asyncio.run(create_schema())
