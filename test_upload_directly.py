#!/usr/bin/env python3
"""
Test upload directly to see what error occurs
"""

import os
import sys
import asyncio
from datetime import datetime
import uuid

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def test_upload():
    """Test inserting a document directly"""
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING")
    if not db_url:
        print("❌ No DATABASE_URL found")
        return
        
    # Convert to async URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print("🔧 Testing direct upload to database...")
    
    try:
        # Create async engine
        engine = create_async_engine(db_url, echo=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create test document data
            doc_id = str(uuid.uuid4())
            user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"  # Your user ID from logs
            institution_id = "default"
            filename = "test-upload.pdf"
            
            print(f"\n📄 Attempting to insert document:")
            print(f"   ID: {doc_id}")
            print(f"   User ID: {user_id}")
            print(f"   Institution ID: {institution_id}")
            print(f"   Filename: {filename}")
            
            # Try the exact insert from the code
            await session.execute(
                text("""
                    INSERT INTO documents (
                        id, user_id, institution_id, filename, file_key, 
                        file_size, content_type, sha256, status, uploaded_at,
                        original_filename, file_path, mime_type
                    ) VALUES (
                        :id, :user_id, :institution_id, :filename, :file_key,
                        :file_size, :content_type, :sha256, :status, :uploaded_at,
                        :original_filename, :file_path, :mime_type
                    )
                """),
                {
                    "id": doc_id,
                    "user_id": user_id,
                    "institution_id": institution_id,
                    "filename": filename,
                    "file_key": f"org/{institution_id}/user/{user_id}/test-upload.pdf",
                    "file_size": 1234567,
                    "content_type": "application/pdf",
                    "sha256": "test-hash-direct",
                    "status": "uploaded",
                    "uploaded_at": datetime.utcnow(),
                    "original_filename": filename,
                    "file_path": f"org/{institution_id}/user/{user_id}/test-upload.pdf",
                    "mime_type": "application/pdf"
                }
            )
            
            await session.commit()
            print("\n✅ Document inserted successfully!")
            
            # Verify it was saved
            result = await session.execute(text("""
                SELECT id, filename, user_id, institution_id, uploaded_at 
                FROM documents 
                WHERE id = :id
            """), {"id": doc_id})
            
            row = result.fetchone()
            if row:
                print(f"\n✅ Document verified in database:")
                print(f"   ID: {row[0]}")
                print(f"   Filename: {row[1]}")
                print(f"   User: {row[2]}")
                print(f"   Institution: {row[3]}")
                print(f"   Uploaded: {row[4]}")
            
            # Don't delete - keep it for testing
            print("\n✅ Test document left in database for verification")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upload())