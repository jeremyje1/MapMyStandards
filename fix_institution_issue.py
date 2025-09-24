#!/usr/bin/env python3
"""
Fix the institution issue by checking what institutions exist
"""

import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

print("🔍 Checking institutions...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check what institutions exist
    print("\n📋 Existing institutions:")
    cursor.execute("""
        SELECT id, name 
        FROM institutions 
        ORDER BY name
    """)
    
    institutions = cursor.fetchall()
    if institutions:
        for inst in institutions:
            print(f"  - ID: {inst[0]}, Name: {inst[1]}")
    else:
        print("  ❌ No institutions found!")
        
    # Check if 'default' institution exists
    cursor.execute("""
        SELECT id FROM institutions WHERE id = 'default'
    """)
    
    if not cursor.fetchone():
        print("\n🔧 Creating 'default' institution...")
        cursor.execute("""
            INSERT INTO institutions (id, name) 
            VALUES ('default', 'Default Institution')
        """)
        conn.commit()
        print("✅ Created 'default' institution")
    else:
        print("\n✅ 'default' institution already exists")
        
    # Check user's institution
    print("\n👤 Checking user's institution:")
    cursor.execute("""
        SELECT u.id, u.email, u.institution_id, i.name
        FROM users u
        LEFT JOIN institutions i ON u.institution_id = i.id
        WHERE u.id = 'e144cf90-d8ed-4277-bf12-3d86443e2099'
    """)
    
    user = cursor.fetchone()
    if user:
        print(f"  User ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Institution ID: {user[2]}")
        print(f"  Institution Name: {user[3]}")
        
        # Return the correct institution_id to use
        if user[2]:
            print(f"\n✅ Use institution_id: '{user[2]}' for uploads")
        else:
            print(f"\n⚠️  User has no institution_id set")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("\n✅ Check complete!")