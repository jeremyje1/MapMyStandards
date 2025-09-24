#!/usr/bin/env python3
"""
Fix documents table schema to match what the code expects
"""

import os
import sys
import logging
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or use default"""
    url = os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING") or "sqlite:///a3e.db"
    # Railway uses postgresql:// but SQLAlchemy needs postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def fix_documents_schema():
    """Add missing columns to documents table"""
    
    # Setup database
    db_url = get_database_url()
    # Use sync engine for schema changes
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Check current columns
        logger.info("Checking current documents table schema...")
        
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
        """))
        
        existing_columns = [row[0] for row in result]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        if 'file_key' not in existing_columns:
            logger.info("Adding file_key column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS file_key VARCHAR(500)
            """))
            conn.commit()
        
        if 'user_id' not in existing_columns:
            logger.info("Adding user_id column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)
            """))
            conn.commit()
        
        if 'organization_id' not in existing_columns:
            logger.info("Adding organization_id column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255)
            """))
            conn.commit()
            
        if 'file_size' not in existing_columns:
            logger.info("Adding file_size column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0
            """))
            conn.commit()
            
        if 'content_type' not in existing_columns:
            logger.info("Adding content_type column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS content_type VARCHAR(100)
            """))
            conn.commit()
            
        if 'sha256' not in existing_columns:
            logger.info("Adding sha256 column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64)
            """))
            conn.commit()
            
        if 'status' not in existing_columns:
            logger.info("Adding status column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'uploaded'
            """))
            conn.commit()
            
        if 'uploaded_at' not in existing_columns:
            logger.info("Adding uploaded_at column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
            
        if 'deleted_at' not in existing_columns:
            logger.info("Adding deleted_at column...")
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
            """))
            conn.commit()
        
        # Verify final schema
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
            ORDER BY ordinal_position
        """))
        
        logger.info("\n✅ Final schema:")
        for col_name, data_type in result:
            logger.info(f"  - {col_name}: {data_type}")
        
        logger.info("\n✅ Schema fixed successfully!")

if __name__ == "__main__":
    try:
        fix_documents_schema()
    except Exception as e:
        logger.error(f"Failed to fix schema: {e}")
        sys.exit(1)