#!/usr/bin/env python3
"""
Clear test users from Railway production database
"""

import subprocess
import json
import sys

def run_railway_query(sql):
    """Execute SQL query on Railway database"""
    try:
        # Use railway run to execute SQL
        result = subprocess.run([
            'railway', 'run', 
            'python3', '-c', 
            f'''
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from Railway
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not found")
    exit(1)

# Parse database URL  
parsed = urlparse(db_url)

# Connect to database
conn = psycopg2.connect(
    host=parsed.hostname,
    database=parsed.path[1:],  # Remove leading slash
    user=parsed.username,
    password=parsed.password,
    port=parsed.port
)

cursor = conn.cursor()
cursor.execute("{sql}")

if "{sql}".upper().startswith("SELECT"):
    results = cursor.fetchall()
    for row in results:
        print(row)
else:
    conn.commit()
    print(f"Query executed successfully. Rows affected: {{cursor.rowcount}}")

cursor.close()
conn.close()
'''
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        else:
            print(result.stdout)
            return True
            
    except Exception as e:
        print(f"❌ Error running Railway query: {e}")
        return False

def clear_users():
    """Clear all users from the production database"""
    print("🔍 Checking for users in production database...")
    
    # First, check how many users exist
    if not run_railway_query("SELECT COUNT(*) as user_count FROM users"):
        return
    
    print("\n📋 Listing all users...")
    if not run_railway_query("SELECT email, created_at FROM users ORDER BY created_at DESC"):
        return
    
    # Confirm deletion
    confirm = input("\n⚠️ Do you want to DELETE ALL users from the production database? (type 'DELETE ALL' to confirm): ")
    
    if confirm == 'DELETE ALL':
        print("🗑️ Deleting all users...")
        if run_railway_query("DELETE FROM users"):
            print("✅ All users have been deleted from the production database")
        else:
            print("❌ Failed to delete users")
    else:
        print("❌ Operation cancelled - users were not deleted")

if __name__ == "__main__":
    print("🚂 Railway Production Database User Cleanup")
    print("=" * 50)
    clear_users()