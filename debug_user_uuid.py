#!/usr/bin/env python3
"""Debug user UUID issues in production"""

import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from Railway environment
DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL_RAILWAY"))

if not DATABASE_URL:
    print("ERROR: No DATABASE_URL found in environment")
    exit(1)

print(f"Connecting to database...")

# Create synchronous engine for debugging
engine = create_engine(DATABASE_URL.replace("asyncpg://", "postgresql://"))

print("\nChecking user data in production database...")
print("=" * 80)

with engine.connect() as conn:
    # Check if there's a user with the email the customer is using
    result = conn.execute(text("""
        SELECT id, email, name, institution, created_at
        FROM users
        WHERE email ILIKE '%jeremy%' OR email ILIKE '%estrella%'
        ORDER BY created_at DESC
        LIMIT 10
    """))
    
    users = result.fetchall()
    print(f"\nFound {len(users)} users matching 'jeremy' or 'estrella':")
    for user in users:
        print(f"\n  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.name}")
        print(f"  Institution: {user.institution}")
        print(f"  Created: {user.created_at}")
    
    # Check recent uploads
    print("\n" + "=" * 80)
    print("Recent uploads (last 10):")
    result = conn.execute(text("""
        SELECT 
            u.id as upload_id,
            u.user_id,
            u.filename,
            u.created_at,
            u.status,
            usr.email,
            COUNT(du.id) as document_count
        FROM uploads u
        LEFT JOIN users usr ON u.user_id = usr.id
        LEFT JOIN documents_upload du ON u.id = du.upload_id
        GROUP BY u.id, u.user_id, u.filename, u.created_at, u.status, usr.email
        ORDER BY u.created_at DESC
        LIMIT 10
    """))
    
    uploads = result.fetchall()
    for upload in uploads:
        print(f"\n  Upload ID: {upload.upload_id}")
        print(f"  User ID: {upload.user_id}")
        print(f"  Email: {upload.email}")
        print(f"  Filename: {upload.filename}")
        print(f"  Status: {upload.status}")
        print(f"  Documents: {upload.document_count}")
        print(f"  Created: {upload.created_at}")
    
    # Check specific document
    doc_id = "440cc1fa-2d43-4b6a-b238-fd2a13025c9f"
    print("\n" + "=" * 80)
    print(f"Checking specific document: {doc_id}")
    
    result = conn.execute(text("""
        SELECT 
            du.id,
            du.document_id,
            du.upload_id,
            u.user_id,
            u.filename,
            usr.email
        FROM documents_upload du
        JOIN uploads u ON du.upload_id = u.id
        LEFT JOIN users usr ON u.user_id = usr.id
        WHERE du.document_id = :doc_id
    """), {"doc_id": doc_id})
    
    doc = result.fetchone()
    if doc:
        print(f"  Found document!")
        print(f"  Upload ID: {doc.upload_id}")
        print(f"  User ID: {doc.user_id}")
        print(f"  User Email: {doc.email}")
        print(f"  Filename: {doc.filename}")
    else:
        print("  Document not found in documents_upload table")
        
        # Check documents table
        result = conn.execute(text("""
            SELECT id, title, content_type, created_at
            FROM documents
            WHERE id = :doc_id
        """), {"doc_id": doc_id})
        
        doc = result.fetchone()
        if doc:
            print(f"  But found in documents table:")
            print(f"  Title: {doc.title}")
            print(f"  Type: {doc.content_type}")
            print(f"  Created: {doc.created_at}")

print("\n" + "=" * 80)
print("If user email doesn't match any users above, they may not be logged in")
print("or using a different email address.")