#!/usr/bin/env python3
"""
Check for recent upload attempts in the database
"""

import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found. Run with: railway run python3 check_recent_uploads.py")
    exit(1)

print("🔍 Checking for recent upload attempts...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check all documents
    print("\n📋 All documents in database:")
    cursor.execute("""
        SELECT id, user_id, institution_id, filename, uploaded_at, file_key
        FROM documents 
        ORDER BY uploaded_at DESC 
        LIMIT 10
    """)
    
    documents = cursor.fetchall()
    if documents:
        for doc in documents:
            print(f"\n  Document: {doc[3]}")
            print(f"  ID: {doc[0]}")
            print(f"  User: {doc[1]}")
            print(f"  Institution: {doc[2]}")
            print(f"  Uploaded: {doc[4]}")
            print(f"  File Key: {doc[5]}")
    else:
        print("  ❌ No documents found!")
    
    # Check for documents in last hour
    print(f"\n⏰ Documents uploaded in last hour (after {datetime.now() - timedelta(hours=1)}):")
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cursor.execute("""
        SELECT filename, uploaded_at, user_id
        FROM documents 
        WHERE uploaded_at > %s
        ORDER BY uploaded_at DESC
    """, (one_hour_ago,))
    
    recent = cursor.fetchall()
    if recent:
        for doc in recent:
            print(f"  - {doc[0]} at {doc[1]} by user {doc[2]}")
    else:
        print("  ❌ No uploads in the last hour")
        
    # Check table structure
    print("\n🔧 Checking table structure:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        AND column_name IN ('institution_id', 'user_id', 'file_key', 'original_filename', 'file_path')
        ORDER BY ordinal_position
    """)
    
    for col in cursor.fetchall():
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Check complete!")