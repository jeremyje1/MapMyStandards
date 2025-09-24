#!/usr/bin/env python3
"""
Test database connection and document insertion
"""

import os
import sys
import asyncio
from datetime import datetime
import uuid

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def test_database():
    """Test database connection and document insertion"""
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING")
    if not db_url:
        print("❌ No DATABASE_URL found")
        return
        
    # Convert to async URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"🔧 Connecting to database...")
    
    try:
        # Create async engine
        engine = create_async_engine(db_url, echo=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Test connection
            result = await session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check documents table
            result = await session.execute(text("""
                SELECT COUNT(*) FROM documents
            """))
            count = result.scalar()
            print(f"📊 Current document count: {count}")
            
            # Try to insert a test document
            test_id = str(uuid.uuid4())
            test_user = "test-user-" + str(uuid.uuid4())[:8]
            
            print("\n🔧 Attempting to insert test document...")
            
            await session.execute(text("""
                INSERT INTO documents (
                    id, user_id, organization_id, filename, file_key,
                    file_size, content_type, sha256, status, uploaded_at
                ) VALUES (
                    :id, :user_id, :org_id, :filename, :file_key,
                    :file_size, :content_type, :sha256, :status, :uploaded_at
                )
            """), {
                "id": test_id,
                "user_id": test_user,
                "org_id": "test-org",
                "filename": "test-document.pdf",
                "file_key": f"test/{test_user}/test-document.pdf",
                "file_size": 12345,
                "content_type": "application/pdf",
                "sha256": "test-hash-123",
                "status": "uploaded",
                "uploaded_at": datetime.utcnow()
            })
            
            await session.commit()
            print("✅ Test document inserted successfully!")
            
            # Verify it was saved
            result = await session.execute(text("""
                SELECT id, filename, user_id, uploaded_at 
                FROM documents 
                WHERE id = :id
            """), {"id": test_id})
            
            row = result.fetchone()
            if row:
                print(f"\n✅ Document verified in database:")
                print(f"  - ID: {row[0]}")
                print(f"  - Filename: {row[1]}")
                print(f"  - User ID: {row[2]}")
                print(f"  - Uploaded: {row[3]}")
            else:
                print("❌ Document not found after insert!")
                
            # Clean up test document
            await session.execute(text("""
                DELETE FROM documents WHERE id = :id
            """), {"id": test_id})
            await session.commit()
            print("\n🧹 Test document cleaned up")
            
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_database())