#!/usr/bin/env python3
"""
Migrate upload data from JSON to PostgreSQL database
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from a3e.models import Base  # noqa: E402
from a3e.models.document import Document  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING") or "sqlite:///a3e.db"

def migrate_uploads_to_database():
    """Migrate uploads from JSON file to database"""
    
    # Setup database
    engine = create_engine(get_database_url())
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Load existing uploads
    uploads_file = os.getenv("USER_UPLOADS_STORE", "user_uploads_store.json")
    
    if not os.path.exists(uploads_file):
        logger.info(f"No uploads file found at {uploads_file}")
        return
    
    try:
        with open(uploads_file, 'r') as f:
            all_uploads = json.load(f)
        
        logger.info(f"Found {len(all_uploads)} users with uploads")
        
        migrated_count = 0
        
        for user_key, user_data in all_uploads.items():
            # Extract user_id from key (format: "user_{id}" or "sub_{id}")
            if user_key.startswith("user_"):
                user_id = user_key[5:]
            elif user_key.startswith("sub_"):
                user_id = user_key[4:]
            else:
                user_id = user_key
            
            documents = user_data.get("documents", [])
            
            for doc in documents:
                # Check if document already exists
                existing = session.query(Document).filter_by(
                    filename=doc.get("filename"),
                    user_id=user_id
                ).first()
                
                if existing:
                    logger.debug(f"Document already exists: {doc.get('filename')} for user {user_id}")
                    continue
                
                # Create new document record
                new_doc = Document(
                    user_id=user_id,
                    filename=doc.get("filename", "unknown"),
                    file_key=doc.get("saved_path", ""),
                    file_size=doc.get("size", 0),
                    content_type=doc.get("doc_type", "application/octet-stream"),
                    sha256=doc.get("fingerprint", ""),
                    status="analyzed" if doc.get("standards_mapped") else "uploaded",
                    uploaded_at=datetime.fromisoformat(doc.get("uploaded_at", datetime.utcnow().isoformat()))
                )
                
                session.add(new_doc)
                migrated_count += 1
                
                logger.info(f"Migrated: {new_doc.filename} for user {user_id}")
        
        session.commit()
        logger.info(f"✅ Successfully migrated {migrated_count} documents to database")
        
        # Optionally rename the JSON file to indicate it's been migrated
        backup_name = uploads_file + ".migrated_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(uploads_file, backup_name)
        logger.info(f"Renamed {uploads_file} to {backup_name}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise

if __name__ == "__main__":
    migrate_uploads_to_database()
