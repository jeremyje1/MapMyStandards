#!/usr/bin/env python3
"""Verify documents for specific user"""

import os
import asyncio
from sqlalchemy import text
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.a3e.database.connection import db_manager

USER_ID = "e144cf90-d8ed-4277-bf12-3d86443e2099"

async def verify_documents():
    """Check documents for the specific user"""
    
    # Initialize database
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        print(f"\n=== CHECKING DOCUMENTS FOR USER: {USER_ID} ===\n")
        
        # Count documents
        result = await session.execute(
            text("""
                SELECT COUNT(*) as count 
                FROM documents 
                WHERE user_id = :user_id 
                AND deleted_at IS NULL
            """),
            {"user_id": USER_ID}
        )
        count = result.scalar()
        print(f"Total documents for this user: {count}")
        
        # Get document details
        result = await session.execute(
            text("""
                SELECT id, filename, file_key, uploaded_at, status
                FROM documents 
                WHERE user_id = :user_id 
                AND deleted_at IS NULL
                ORDER BY uploaded_at DESC
            """),
            {"user_id": USER_ID}
        )
        
        print("\nDocument Details:")
        for row in result:
            print(f"\n- ID: {row.id}")
            print(f"  Filename: {row.filename}")
            print(f"  File Key: {row.file_key}")
            print(f"  Uploaded: {row.uploaded_at}")
            print(f"  Status: {row.status}")
        
        # Check if there are any documents with NULL user_id
        result = await session.execute(
            text("SELECT COUNT(*) FROM documents WHERE user_id IS NULL")
        )
        null_count = result.scalar()
        if null_count > 0:
            print(f"\n⚠️  Found {null_count} documents with NULL user_id")
        
        # Check recently uploaded documents (last hour)
        result = await session.execute(
            text("""
                SELECT filename, user_id, uploaded_at 
                FROM documents 
                WHERE uploaded_at > NOW() - INTERVAL '1 hour'
                ORDER BY uploaded_at DESC
            """)
        )
        
        print("\n=== RECENT UPLOADS (Last Hour) ===")
        recent = list(result)
        if recent:
            for row in recent:
                print(f"- {row.filename} (user: {row.user_id[:8] if row.user_id else 'NULL'}..., {row.uploaded_at})")
        else:
            print("No uploads in the last hour")

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found. Run with: railway run python3 verify_user_documents.py")
        exit(1)
    
    asyncio.run(verify_documents())