#!/usr/bin/env python3
"""
Check the documents table schema in Railway database
"""
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from Railway environment
database_url = "postgresql://postgres:WKdMFqDTqgdSbINQXGSDrLKlgJBLcLdN@junction.proxy.rlwy.net:51068/railway"

# Parse the URL
parsed = urlparse(database_url)

try:
    # Connect to the database
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:],  # Remove leading '/'
        sslmode='require'
    )
    
    cur = conn.cursor()
    
    # Get columns from documents table
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'documents'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    
    print("=== DOCUMENTS TABLE SCHEMA ===")
    if columns:
        for col in columns:
            print(f"  {col[0]:30} {col[1]:20} {col[2]}")
    else:
        print("  Documents table not found or has no columns")
    
    # Check if evidence_mappings table exists
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'evidence_mappings'
        ORDER BY ordinal_position;
    """)
    
    mappings_cols = cur.fetchall()
    
    print("\n=== EVIDENCE_MAPPINGS TABLE SCHEMA ===")
    if mappings_cols:
        for col in mappings_cols:
            print(f"  {col[0]:30} {col[1]:20} {col[2]}")
    else:
        print("  Evidence_mappings table not found or has no columns")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")