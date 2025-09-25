#!/usr/bin/env python3
"""
Ensure documents table exists in the database with correct schema
"""

import os
import sys
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine, text  # noqa: E402
from a3e.models import Base  # noqa: E402
from a3e.models.document import Document  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING") or "sqlite:///a3e.db"

def ensure_documents_table():
    """Ensure documents table exists with proper schema"""
    
    # Setup database
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    # Create tables from models
    logger.info(f"Creating documents table in database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    Base.metadata.create_all(bind=engine, tables=[Document.__table__])
    
    # Verify table exists
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'documents'
        """))
        
        if result.scalar() > 0:
            logger.info("✅ Documents table exists")
            
            # Check column existence
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents'
            """))
            
            columns = [row[0] for row in result]
            logger.info(f"Columns: {', '.join(columns)}")
            
            # Count existing documents
            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            count = result.scalar()
            logger.info(f"Existing documents: {count}")
        else:
            logger.error("❌ Documents table does not exist!")

if __name__ == "__main__":
    ensure_documents_table()
