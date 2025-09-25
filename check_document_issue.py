#!/usr/bin/env python3
"""Check what's happening with the document IDs"""

import psycopg2
import os
import json

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: No database URL found in environment variables")
    print("Please set DATABASE_URL or DATABASE_PUBLIC_URL")
    exit(1)

print("Checking document IDs in database...")
print("=" * 60)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check documents table
    print("\n1. All documents in database:")
    cursor.execute("""
        SELECT id, filename, user_id, status, uploaded_at, file_key
        FROM documents 
        WHERE deleted_at IS NULL
        ORDER BY uploaded_at DESC
        LIMIT 10
    """)
    
    documents = cursor.fetchall()
    print(f"   Found {len(documents)} documents")
    for doc in documents:
        print(f"\n   ID: {doc[0]}")
        print(f"   Filename: {doc[1]}")
        print(f"   User: {doc[2]}")
        print(f"   Status: {doc[3]}")
        print(f"   Uploaded: {doc[4]}")
        print(f"   File Key: {doc[5]}")
    
    # Check for the specific document ID from the error
    error_id = "9cdee4fa-74fd-4cb3-8e9a-ee32c33f3020"
    print(f"\n2. Checking for document ID from error: {error_id}")
    cursor.execute("""
        SELECT * FROM documents WHERE id = %s
    """, (error_id,))
    
    result = cursor.fetchone()
    if result:
        print("   ✓ Document found!")
        print(f"   Details: {result}")
    else:
        print("   ✗ Document NOT found in database")
        print("   This ID might be a hash/fingerprint, not a database ID")
    
    # Check if this might be a sha256 hash
    print(f"\n3. Checking if this is a SHA256 hash...")
    cursor.execute("""
        SELECT id, filename, sha256 FROM documents 
        WHERE sha256 = %s OR sha256 LIKE %s
    """, (error_id, f"%{error_id}%"))
    
    results = cursor.fetchall()
    if results:
        print("   Found documents with matching SHA256:")
        for r in results:
            print(f"   ID: {r[0]}, File: {r[1]}, SHA256: {r[2]}")
    else:
        print("   No documents found with this SHA256")
    
    # Show recent uploads for Jeremy
    print("\n4. Recent uploads for jeremy.estrella@gmail.com:")
    cursor.execute("""
        SELECT id, filename, status, uploaded_at
        FROM documents 
        WHERE user_id = 'jeremy.estrella@gmail.com'
        AND deleted_at IS NULL
        ORDER BY uploaded_at DESC
        LIMIT 5
    """)
    
    jeremy_docs = cursor.fetchall()
    for doc in jeremy_docs:
        print(f"\n   ID: {doc[0]}")
        print(f"   File: {doc[1]}")
        print(f"   Status: {doc[2]}")
        print(f"   Uploaded: {doc[3]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Database error: {e}")
    
print("\n" + "=" * 60)
print("ANALYSIS:")
print("The frontend is trying to use document IDs that don't exist in the database.")
print("This could be because:")
print("1. The frontend is caching old IDs from a previous session")
print("2. The IDs are being generated client-side instead of using server IDs")
print("3. There's a mismatch between what /uploads returns and what the frontend expects")
print("\nSOLUTION: The frontend should use the 'id' field from the /uploads response")