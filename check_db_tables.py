#!/usr/bin/env python3
"""Check database tables and structure"""

import psycopg2
from urllib.parse import urlparse

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

print("Checking database structure...")
print("=" * 60)

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check for document-related tables
    doc_tables = [t[0] for t in tables if 'doc' in t[0].lower() or 'upload' in t[0].lower()]
    
    if doc_tables:
        print(f"\nDocument/Upload related tables:")
        for table in doc_tables:
            print(f"\n  Table: {table}")
            # Get columns
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            columns = cur.fetchall()
            for col in columns[:5]:  # Show first 5 columns
                print(f"    - {col[0]}: {col[1]}")
    
    # Check if document 440cc1fa exists anywhere
    doc_id = "440cc1fa-2d43-4b6a-b238-fd2a13025c9f"
    print(f"\n" + "=" * 60)
    print(f"Searching for document {doc_id}...")
    
    # Try documents table
    if 'documents' in [t[0] for t in tables]:
        cur.execute("SELECT COUNT(*) FROM documents WHERE id = %s", (doc_id,))
        count = cur.fetchone()[0]
        print(f"  In 'documents' table: {'Yes' if count > 0 else 'No'}")
    
    # Try uploads table with document_id
    if 'uploads' in [t[0] for t in tables]:
        # Check if uploads has document_id column
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'uploads' AND column_name LIKE '%doc%'
        """)
        doc_cols = cur.fetchall()
        if doc_cols:
            print(f"  'uploads' table has document columns: {[c[0] for c in doc_cols]}")
    
    # Check Jeremy's data
    print(f"\n" + "=" * 60)
    print(f"Checking Jeremy's data...")
    jeremy_user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"
    
    # Check if user exists
    cur.execute("SELECT id, email, name FROM users WHERE id = %s", (jeremy_user_id,))
    user = cur.fetchone()
    if user:
        print(f"  User found: {user[1]} ({user[2]})")
        
        # Check uploads
        if 'uploads' in [t[0] for t in tables]:
            cur.execute("SELECT COUNT(*) FROM uploads WHERE user_id = %s", (jeremy_user_id,))
            upload_count = cur.fetchone()[0]
            print(f"  Total uploads: {upload_count}")
            
            if upload_count > 0:
                cur.execute("""
                    SELECT id, filename, status, created_at 
                    FROM uploads 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """, (jeremy_user_id,))
                uploads = cur.fetchall()
                print(f"\n  Recent uploads:")
                for upload in uploads:
                    print(f"    - {upload[1]} ({upload[2]}) - {upload[3]}")
    else:
        print(f"  User not found!")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)