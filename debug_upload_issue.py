#!/usr/bin/env python3
"""
Debug why uploads aren't showing up
"""

import os
import psycopg2
from datetime import datetime, timedelta

# Railway provides these environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found. Run with: railway run python3 debug_upload_issue.py")
    exit(1)

print("🔍 Debugging upload issue...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check all documents in the table
    print("\n📋 All documents in the table:")
    cursor.execute("""
        SELECT id, user_id, filename, file_key, uploaded_at, status
        FROM documents 
        ORDER BY uploaded_at DESC 
        LIMIT 20
    """)
    
    documents = cursor.fetchall()
    if documents:
        for doc in documents:
            print(f"  - ID: {doc[0]}")
            print(f"    User: {doc[1]}")
            print(f"    File: {doc[2]}")
            print(f"    Key: {doc[3]}")
            print(f"    Uploaded: {doc[4]}")
            print(f"    Status: {doc[5]}")
            print()
    else:
        print("  No documents found in table")
    
    # Check recent upload attempts (last hour)
    print("\n⏰ Documents uploaded in last hour:")
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cursor.execute("""
        SELECT id, user_id, filename, uploaded_at
        FROM documents 
        WHERE uploaded_at > %s
        ORDER BY uploaded_at DESC
    """, (one_hour_ago,))
    
    recent = cursor.fetchall()
    if recent:
        for doc in recent:
            print(f"  - {doc[2]} (uploaded {doc[3]})")
    else:
        print("  No recent uploads")
    
    # Check if user_id column has any data
    print("\n👤 Checking user_id values:")
    cursor.execute("""
        SELECT DISTINCT user_id, COUNT(*) as count
        FROM documents 
        GROUP BY user_id
    """)
    
    user_counts = cursor.fetchall()
    if user_counts:
        for user_id, count in user_counts:
            print(f"  - User {user_id}: {count} documents")
    else:
        print("  No user_id values found")
    
    # Check column data types
    print("\n🔧 Column info for key fields:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        AND column_name IN ('id', 'user_id', 'file_key', 'filename', 'uploaded_at', 'deleted_at')
        ORDER BY ordinal_position
    """)
    
    for col in cursor.fetchall():
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Debug complete!")
