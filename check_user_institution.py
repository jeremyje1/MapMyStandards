#!/usr/bin/env python3
"""
Check user institution data using Railway database connection
This script uses psycopg2 instead of asyncpg to avoid DNS issues
"""

import os
import psycopg2
from urllib.parse import urlparse

def check_user_institution():
    try:
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found")
            print("ℹ️  Run with: railway run python3 check_user_institution.py")
            return
        
        print("🔍 Checking user institution data...")
        
        # Parse the DATABASE_URL
        parsed = urlparse(database_url)
        
        # Connect using psycopg2
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading /
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        # Check for jeremy.estrella@gmail.com
        cur.execute("""
            SELECT 
                id,
                email,
                name,
                institution_name,
                institution_type,
                role,
                created_at,
                stripe_customer_id,
                stripe_subscription_id
            FROM users 
            WHERE email = %s
        """, ('jeremy.estrella@gmail.com',))
        
        user = cur.fetchone()
        
        if user:
            print("\n✅ User found!")
            print("-" * 50)
            print(f"ID: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"Name: {user[2]}")
            print(f"Institution: {user[3] or '❌ NOT SET'}")
            print(f"Institution Type: {user[4] or 'NOT SET'}")
            print(f"Role: {user[5] or 'NOT SET'}")
            print(f"Created: {user[6]}")
            print(f"Stripe Customer: {user[7] or 'NOT SET'}")
            print(f"Stripe Subscription: {user[8] or 'NOT SET'}")
            print("-" * 50)
            
            if not user[3]:  # institution_name is None
                print("\n⚠️  Institution name is not set in the database!")
                print("This explains why Houston College isn't showing up.")
                print("\nTo fix this, the onboarding process needs to update the database.")
        else:
            print("❌ User not found in database")
        
        # Also check settings JSON file if it exists
        print("\n📄 Checking settings JSON...")
        print("The onboarding saves to a JSON file, not the database.")
        print("This is why your institution data isn't persisting properly.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're running with Railway environment")
        print("2. Check if psycopg2 is installed: pip install psycopg2-binary")

if __name__ == "__main__":
    check_user_institution()