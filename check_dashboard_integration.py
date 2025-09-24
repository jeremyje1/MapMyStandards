#!/usr/bin/env python3
"""Check why documents aren't appearing on the main dashboard"""

import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.a3e.database.connection import db_manager

async def check_dashboard_integration():
    """Check documents table and how they should appear on dashboard"""
    
    # Initialize database first
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Check all documents
        print("\n=== ALL DOCUMENTS IN DATABASE ===")
        result = await session.execute(
            text("""
                SELECT id, filename, user_id, organization_id, institution_id,
                       file_key, uploaded_at, status, deleted_at
                FROM documents 
                ORDER BY uploaded_at DESC
                LIMIT 20
            """)
        )
        
        docs = []
        for row in result:
            docs.append({
                'id': row.id,
                'filename': row.filename,
                'user_id': row.user_id,
                'organization_id': row.organization_id,
                'institution_id': row.institution_id,
                'file_key': row.file_key,
                'uploaded_at': row.uploaded_at,
                'status': row.status,
                'deleted_at': row.deleted_at
            })
            print(f"\nDocument ID: {row.id}")
            print(f"  Filename: {row.filename}")
            print(f"  User ID: {row.user_id}")
            print(f"  Organization ID: {row.organization_id}")
            print(f"  Institution ID: {row.institution_id}")
            print(f"  File Key: {row.file_key}")
            print(f"  Uploaded At: {row.uploaded_at}")
            print(f"  Status: {row.status}")
            print(f"  Deleted: {row.deleted_at}")
        
        # Check if there are user_intelligence_evidence entries
        print("\n=== USER INTELLIGENCE EVIDENCE TABLE ===")
        result = await session.execute(
            text("""
                SELECT COUNT(*) as count FROM user_intelligence_evidence
            """)
        )
        count = result.scalar()
        print(f"Total entries in user_intelligence_evidence: {count}")
        
        if count > 0:
            result = await session.execute(
                text("""
                    SELECT user_id, evidence_id, filename, uploaded_at
                    FROM user_intelligence_evidence
                    ORDER BY uploaded_at DESC
                    LIMIT 10
                """)
            )
            
            print("\nRecent user_intelligence_evidence entries:")
            for row in result:
                print(f"  User: {row.user_id}, File: {row.filename}, Uploaded: {row.uploaded_at}")
        
        # Check user_mappings table
        print("\n=== USER MAPPINGS TABLE ===")
        result = await session.execute(
            text("""
                SELECT COUNT(*) as count FROM user_mappings
            """)
        )
        count = result.scalar()
        print(f"Total entries in user_mappings: {count}")
        
        # Dashboard query simulation
        print("\n=== SIMULATING DASHBOARD QUERY ===")
        # This is what the dashboard might be looking for
        result = await session.execute(
            text("""
                SELECT DISTINCT d.* 
                FROM documents d
                WHERE d.deleted_at IS NULL
                AND d.status = 'uploaded'
                ORDER BY d.uploaded_at DESC
                LIMIT 10
            """)
        )
        
        dashboard_docs = []
        for row in result:
            dashboard_docs.append(row.filename)
            
        print(f"Documents visible to dashboard: {len(dashboard_docs)}")
        for filename in dashboard_docs:
            print(f"  - {filename}")
        
        return docs

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found. Run with: railway run python3 check_dashboard_integration.py")
        exit(1)
    
    asyncio.run(check_dashboard_integration())