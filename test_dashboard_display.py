#!/usr/bin/env python3
"""Check why documents aren't showing on main dashboard"""

import os
import asyncio
from sqlalchemy import text
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.a3e.database.connection import db_manager

async def check_dashboard_docs():
    """Check what the dashboard should be showing"""
    
    # Initialize database
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Count all documents
        result = await session.execute(
            text("SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL")
        )
        total = result.scalar()
        print(f"\nTotal active documents in database: {total}")
        
        # Get recent documents
        result = await session.execute(
            text("""
                SELECT id, filename, user_id, uploaded_at, status
                FROM documents 
                WHERE deleted_at IS NULL
                ORDER BY uploaded_at DESC
                LIMIT 10
            """)
        )
        
        print("\nRecent documents:")
        for row in result:
            print(f"  - {row.filename} (user: {row.user_id[:8]}..., status: {row.status})")
        
        # Check unique users
        result = await session.execute(
            text("""
                SELECT DISTINCT user_id, COUNT(*) as doc_count
                FROM documents 
                WHERE deleted_at IS NULL
                GROUP BY user_id
            """)
        )
        
        print("\nDocuments per user:")
        for row in result:
            print(f"  - User {row.user_id[:8]}...: {row.doc_count} documents")

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found. Run with: railway run python3 test_dashboard_display.py")
        exit(1)
    
    asyncio.run(check_dashboard_docs())
