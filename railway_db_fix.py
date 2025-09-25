#!/usr/bin/env python3
"""
Fix documents table schema using Railway environment
"""

import os
import psycopg2
from psycopg2 import sql

# Railway provides these environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found. Make sure to run this with 'railway run python railway_db_fix.py'")
    exit(1)

print("🔧 Connecting to Railway database...")

try:
    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    
    # Check current schema
    print("\n📋 Checking current documents table schema...")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    
    existing_columns = cursor.fetchall()
    if existing_columns:
        print("Current columns:")
        for col_name, data_type in existing_columns:
            print(f"  - {col_name}: {data_type}")
    else:
        print("❌ Documents table not found!")
        exit(1)
    
    # Add missing columns
    print("\n🔧 Adding missing columns...")
    
    columns_to_add = [
        ("file_key", "VARCHAR(500)"),
        ("user_id", "VARCHAR(36)"),
        ("organization_id", "VARCHAR(255)"),
        ("file_size", "INTEGER DEFAULT 0"),
        ("content_type", "VARCHAR(100)"),
        ("sha256", "VARCHAR(64)"),
        ("status", "VARCHAR(50) DEFAULT 'uploaded'"),
        ("uploaded_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("deleted_at", "TIMESTAMP")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            print(f"  ✅ Added column: {col_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ℹ️  Column {col_name} already exists")
            else:
                print(f"  ❌ Error adding {col_name}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify final schema
    print("\n✅ Verifying final schema...")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    
    final_columns = cursor.fetchall()
    print("Final columns:")
    for col_name, data_type in final_columns:
        print(f"  - {col_name}: {data_type}")
    
    print("\n🎉 Schema fix complete!")
    
    # Check if there's any data
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    print(f"\n📊 Current document count: {count}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✨ All done! Your uploads should now persist properly.")
