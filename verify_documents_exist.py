#!/usr/bin/env python3
"""
Verify documents exist and can be retrieved
"""

import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

print("🔍 Verifying documents...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"
    
    # Simple query - just check what's there
    print(f"\n📋 Documents for user {user_id}:")
    cursor.execute("""
        SELECT id, filename, uploaded_at, deleted_at
        FROM documents 
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
    """, (user_id,))
    
    documents = cursor.fetchall()
    for doc in documents:
        print(f"\n  File: {doc[1]}")
        print(f"  Uploaded: {doc[2]}")
        print(f"  Deleted: {doc[3]}")
    
    # Now try with deleted_at IS NULL only
    print(f"\n📋 Non-deleted documents:")
    cursor.execute("""
        SELECT id, filename 
        FROM documents 
        WHERE user_id = %s AND deleted_at IS NULL
    """, (user_id,))
    
    active_docs = cursor.fetchall()
    print(f"Found {len(active_docs)} active documents")
    for doc in active_docs:
        print(f"  - {doc[1]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Check complete!")