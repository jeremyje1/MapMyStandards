#!/usr/bin/env python3
"""
Check what happened with the recent upload attempts
"""

import os
import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found. Run with: railway run python3 check_upload_logs.py")
    exit(1)

print("🔍 Checking upload status...")
print(f"Current time: {datetime.now()}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if ANY documents exist
    print("\n📊 Document count check:")
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    print(f"Total documents in database: {count}")
    
    # Check last 10 documents (if any)
    print("\n📋 Last 10 documents (if any):")
    cursor.execute("""
        SELECT id, user_id, institution_id, filename, uploaded_at, file_key, 
               original_filename, file_path, mime_type
        FROM documents 
        ORDER BY uploaded_at DESC 
        LIMIT 10
    """)
    
    documents = cursor.fetchall()
    if documents:
        for doc in documents:
            print(f"\n  Document: {doc[3]}")
            print(f"  ID: {doc[0]}")
            print(f"  User ID: {doc[1]}")
            print(f"  Institution ID: {doc[2]}")
            print(f"  Uploaded: {doc[4]}")
            print(f"  File Key: {doc[5]}")
            print(f"  Original Filename: {doc[6]}")
            print(f"  File Path: {doc[7]}")
            print(f"  MIME Type: {doc[8]}")
    else:
        print("  ❌ No documents found in database!")
        
    # Check for NULL required fields
    print("\n🔍 Checking for problematic NULL values:")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM documents 
        WHERE institution_id IS NULL 
           OR filename IS NULL
           OR original_filename IS NULL
    """)
    null_count = cursor.fetchone()[0]
    print(f"Documents with NULL required fields: {null_count}")
    
    # Check all columns in documents table
    print("\n🔧 All columns in documents table:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    required_cols = []
    for col in columns:
        nullable = "NULLABLE" if col[2] == 'YES' else "REQUIRED"
        print(f"  - {col[0]}: {col[1]} ({nullable})")
        if col[2] == 'NO' and col[3] is None:  # Required without default
            required_cols.append(col[0])
    
    print(f"\n❗ Required columns without defaults: {', '.join(required_cols)}")

except Exception as e:
    print(f"\n❌ Database error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Check complete!")

print("\n💡 If no documents found, the upload might be failing before reaching the database.")
print("   Check Railway logs for any error messages during upload attempts.")