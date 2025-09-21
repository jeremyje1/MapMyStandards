#!/usr/bin/env python3
"""
Update user institution in the database
"""

import psycopg2
import sys

def update_institution(email, new_institution):
    try:
        # Direct connection string
        conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
        
        print(f"🔍 Connecting to database...")
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        # Update the institution
        print(f"📝 Updating institution for {email} to '{new_institution}'...")
        cur.execute("""
            UPDATE users 
            SET institution_name = %s
            WHERE email = %s
            RETURNING id, email, institution_name
        """, (new_institution, email))
        
        updated = cur.fetchone()
        
        if updated:
            print(f"\n✅ Successfully updated!")
            print(f"   User: {updated[1]}")
            print(f"   New Institution: {updated[2]}")
            conn.commit()
        else:
            print(f"❌ No user found with email: {email}")
            conn.rollback()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        # Update to Houston College
        update_institution("jeremy.estrella@gmail.com", "Houston College")
    else:
        print("Institution Update Tool")
        print("=" * 50)
        print("\nCurrent institution: NorthPath Strategies")
        print("Desired institution: Houston College")
        print("\nTo update your institution to Houston College, run:")
        print("  python3 update_user_institution.py --update")
        print("\n⚠️  This will directly modify the database.")

if __name__ == "__main__":
    main()