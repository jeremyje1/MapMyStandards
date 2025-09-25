#!/usr/bin/env python3
"""
Debug why the API returns empty results
"""

import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

print("🔍 Debugging API response issue...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check all documents with their user IDs
    print("\n📋 All documents in database:")
    cursor.execute("""
        SELECT id, user_id, filename, uploaded_at, 
               (deleted_at IS NULL OR deleted_at = '') as not_deleted
        FROM documents 
        ORDER BY uploaded_at DESC
    """)
    
    documents = cursor.fetchall()
    for doc in documents:
        print(f"\n  File: {doc[2]}")
        print(f"  User ID: {doc[1]}")
        print(f"  Uploaded: {doc[3]}")
        print(f"  Not deleted: {doc[4]}")
    
    # Check specifically for user e144cf90-d8ed-4277-bf12-3d86443e2099
    user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"
    print(f"\n🔍 Checking documents for user {user_id}:")
    
    # Try the exact query from the API
    cursor.execute("""
        SELECT id, filename, file_key, file_size, content_type, 
               sha256, status, uploaded_at, organization_id
        FROM documents 
        WHERE user_id = %s 
        AND (deleted_at IS NULL OR deleted_at = '')
        ORDER BY uploaded_at DESC
        LIMIT 50
    """, (user_id,))
    
    user_docs = cursor.fetchall()
    print(f"Found {len(user_docs)} documents for this user")
    
    if not user_docs:
        # Check without the deleted_at condition
        cursor.execute("""
            SELECT id, filename, user_id, deleted_at
            FROM documents 
            WHERE user_id = %s
        """, (user_id,))
        
        all_user_docs = cursor.fetchall()
        print(f"\nWithout deleted_at filter: {len(all_user_docs)} documents")
        
        # Check if deleted_at values are problematic
        cursor.execute("""
            SELECT DISTINCT deleted_at, COUNT(*) 
            FROM documents 
            WHERE user_id = %s
            GROUP BY deleted_at
        """, (user_id,))
        
        deleted_stats = cursor.fetchall()
        print("\nDeleted_at values:")
        for stat in deleted_stats:
            print(f"  {stat[0]}: {stat[1]} documents")
    
    # Check for any user ID issues
    print("\n🔍 Checking all unique user IDs:")
    cursor.execute("""
        SELECT DISTINCT user_id, COUNT(*) as doc_count
        FROM documents
        GROUP BY user_id
        ORDER BY doc_count DESC
    """)
    
    users = cursor.fetchall()
    for user in users:
        print(f"  User: {user[0]} - {user[1]} documents")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Debug complete!")
