#!/usr/bin/env python3
"""Check who owns document 440cc1fa-2d43-4b6a-b238-fd2a13025c9f"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse the DATABASE_URL from Railway
DATABASE_URL = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"

# Parse connection details
url = urlparse(DATABASE_URL)
conn_params = {
    'host': url.hostname,
    'port': url.port,
    'database': url.path[1:],
    'user': url.username,
    'password': url.password
}

print("Checking document ownership...")
print("=" * 60)

try:
    # Connect to database
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Check if document exists
    doc_id = "440cc1fa-2d43-4b6a-b238-fd2a13025c9f"
    jeremy_user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"
    
    print(f"\nLooking for document: {doc_id}")
    print(f"Jeremy's user ID: {jeremy_user_id}")
    
    # Check documents_upload table
    cur.execute("""
        SELECT 
            du.id,
            du.document_id,
            du.upload_id,
            u.user_id,
            u.filename,
            usr.email,
            usr.name
        FROM documents_upload du
        JOIN uploads u ON du.upload_id = u.id
        LEFT JOIN users usr ON u.user_id = usr.id
        WHERE du.document_id = %s
    """, (doc_id,))
    
    result = cur.fetchone()
    if result:
        print(f"\nDocument found in documents_upload!")
        print(f"  Upload ID: {result[2]}")
        print(f"  Owner User ID: {result[3]}")
        print(f"  Owner Email: {result[5]}")
        print(f"  Owner Name: {result[6]}")
        print(f"  Filename: {result[4]}")
        
        if result[3] == jeremy_user_id:
            print(f"\n✓ Document belongs to Jeremy!")
        else:
            print(f"\n✗ Document belongs to a different user")
    else:
        print(f"\nDocument not found in documents_upload table")
        
        # Check if it exists in documents table
        cur.execute("""
            SELECT id, title, content_type, created_at
            FROM documents
            WHERE id = %s
        """, (doc_id,))
        
        doc_result = cur.fetchone()
        if doc_result:
            print(f"\nBut found in documents table:")
            print(f"  Title: {doc_result[1]}")
            print(f"  Type: {doc_result[2]}")
            print(f"  Created: {doc_result[3]}")
            print(f"\nThis document has no upload/user association!")
        else:
            print(f"\nDocument not found in database at all")
    
    # Check Jeremy's uploads
    print(f"\n" + "=" * 60)
    print(f"Checking Jeremy's uploads...")
    
    cur.execute("""
        SELECT 
            u.id,
            u.filename,
            u.status,
            u.created_at,
            COUNT(du.id) as doc_count
        FROM uploads u
        LEFT JOIN documents_upload du ON u.id = du.upload_id
        WHERE u.user_id = %s
        GROUP BY u.id, u.filename, u.status, u.created_at
        ORDER BY u.created_at DESC
        LIMIT 10
    """, (jeremy_user_id,))
    
    uploads = cur.fetchall()
    print(f"\nFound {len(uploads)} uploads for Jeremy:")
    for upload in uploads:
        print(f"\n  Upload ID: {upload[0]}")
        print(f"  Filename: {upload[1]}")
        print(f"  Status: {upload[2]}")
        print(f"  Documents: {upload[4]}")
        print(f"  Created: {upload[3]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)