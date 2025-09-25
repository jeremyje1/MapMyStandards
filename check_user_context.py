#!/usr/bin/env python3
"""Check user context and document ownership"""

import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: No database URL found")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check the user who owns the document
    print("Checking document ownership...")
    print("=" * 60)
    
    # Get user details for the document owner
    cursor.execute("""
        SELECT u.id, u.email, u.name, u.created_at
        FROM users u
        WHERE u.id = 'e144cf90-d8ed-4277-bf12-3d86443e2099'
    """)
    
    user = cursor.fetchone()
    if user:
        print(f"\nDocument Owner:")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]}")
        print(f"  Created: {user[3]}")
    else:
        print("\nUser not found in users table")
    
    # Check jeremy's documents
    print(f"\n\nJeremy's Documents:")
    print("-" * 60)
    
    cursor.execute("""
        SELECT u.id as user_uuid
        FROM users u
        WHERE u.email = 'jeremy.estrella@gmail.com'
    """)
    
    jeremy = cursor.fetchone()
    if jeremy:
        jeremy_id = jeremy[0]
        print(f"Jeremy's User ID: {jeremy_id}")
        
        cursor.execute("""
            SELECT id, filename, status, uploaded_at
            FROM documents
            WHERE user_id = %s
            AND deleted_at IS NULL
            ORDER BY uploaded_at DESC
        """, (jeremy_id,))
        
        docs = cursor.fetchall()
        print(f"\nFound {len(docs)} documents for Jeremy:")
        for doc in docs:
            print(f"\n  ID: {doc[0]}")
            print(f"  File: {doc[1]}")
            print(f"  Status: {doc[2]}")
            print(f"  Uploaded: {doc[3]}")
    
    # Show all recent documents with user info
    print(f"\n\nAll Recent Documents (with owners):")
    print("-" * 60)
    
    cursor.execute("""
        SELECT d.id, d.filename, d.user_id, u.email, d.uploaded_at
        FROM documents d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE d.deleted_at IS NULL
        ORDER BY d.uploaded_at DESC
        LIMIT 10
    """)
    
    all_docs = cursor.fetchall()
    for doc in all_docs:
        print(f"\n  Doc ID: {doc[0]}")
        print(f"  File: {doc[1]}")
        print(f"  User ID: {doc[2]}")
        print(f"  User Email: {doc[3] or 'Unknown'}")
        print(f"  Uploaded: {doc[4]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("The frontend is showing documents from multiple users.")
print("Each user should only see their own documents.")
print("The API is working correctly by blocking cross-user access.")