#!/usr/bin/env python3
"""
Check user data using direct database connection
"""

import psycopg2

def check_user_data():
    try:
        # Direct connection string
        conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
        
        print("🔍 Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        # Check for jeremy.estrella@gmail.com
        print("\n👤 Checking user: jeremy.estrella@gmail.com")
        cur.execute("""
            SELECT 
                id,
                email,
                name,
                institution_name,
                institution_type,
                role,
                created_at,
                is_trial,
                stripe_customer_id,
                stripe_subscription_id,
                api_key
            FROM users 
            WHERE email = %s
        """, ('jeremy.estrella@gmail.com',))
        
        user = cur.fetchone()
        
        if user:
            print("\n✅ User found in database!")
            print("=" * 60)
            print(f"ID: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"Name: {user[2]}")
            print(f"Institution: {user[3] if user[3] else '❌ NOT SET (This is the problem!)'}")
            print(f"Institution Type: {user[4] if user[4] else 'NOT SET'}")
            print(f"Role: {user[5] if user[5] else 'NOT SET'}")
            print(f"Created: {user[6]}")
            print(f"Is Trial: {user[7]}")
            print(f"Stripe Customer: {'✅ ' + user[8] if user[8] else '❌ NOT SET'}")
            print(f"Stripe Subscription: {'✅ ' + user[9] if user[9] else '❌ NOT SET'}")
            print(f"API Key: {'✅ SET' if user[10] else '❌ NOT SET'}")
            print("=" * 60)
            
            if not user[3]:  # institution_name is None
                print("\n⚠️  ISSUE FOUND: Institution name is NOT saved in the database!")
                print("This is why 'Houston College' isn't appearing anywhere.")
                print("\nThe onboarding process saves to a JSON file, not the database.")
                print("The user record needs to be updated with the institution_name.")
        else:
            print("❌ User not found in database")
        
        # Check if there are any users with Houston in their institution
        print("\n🔍 Checking for any Houston-related institutions...")
        cur.execute("""
            SELECT email, institution_name 
            FROM users 
            WHERE institution_name ILIKE '%houston%'
        """)
        
        houston_users = cur.fetchall()
        if houston_users:
            print(f"\nFound {len(houston_users)} users with Houston in institution:")
            for u in houston_users:
                print(f"  - {u[0]}: {u[1]}")
        else:
            print("No users found with 'Houston' in their institution name")
        
        # Show total user count
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        print(f"\n📊 Total users in database: {total}")
        
        cur.close()
        conn.close()
        
        print("\n💡 SOLUTION: To fix this issue, we need to:")
        print("1. Update the onboarding to save institution_name to the database")
        print("2. Or manually update your user record with the institution")
        print("3. Create a backend endpoint that properly updates user profiles")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_user_data()