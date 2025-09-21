#!/usr/bin/env python3
"""
Simple script to clear all users from the database.
Handles foreign key constraints by deleting dependent records first.
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main function to clear all users."""
    print("\n⚠️  WARNING: This will DELETE ALL USERS from the database!")
    print("=" * 73)
    
    # Connect to database
    try:
        # Use Railway database URL (production)
        conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True  # Autocommit to avoid transaction issues
    except Exception as e:
        print(f"\n❌ Failed to connect to database: {e}")
        return
    
    with conn.cursor() as cur:
        # Get current user count
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"\n📊 Current user count: {user_count}")
        
        if user_count == 0:
            print("ℹ️  No users to delete.")
            return
        
        # Show users to be deleted
        cur.execute("SELECT email, institution_name FROM users ORDER BY created_at")
        users = cur.fetchall()
        print("\n👥 Users to be deleted:")
        for email, institution in users:
            print(f"   - {email} ({institution or 'No institution'})")
    
    # Confirm deletion
    confirmation = input("\n⚠️  Are you sure you want to delete all users? Type 'DELETE ALL' to confirm: ").strip()
    
    if confirmation != "DELETE ALL":
        print("❌ Cancelled. No users were deleted.")
        return
    
    # Delete all data
    print("\n🗑️  Deleting all users and related data...")
    
    try:
        with conn.cursor() as cur:
            # First delete jobs that reference files
            try:
                cur.execute("DELETE FROM jobs")
                print(f"   ✅ Deleted {cur.rowcount} jobs")
            except Exception as e:
                if "does not exist" not in str(e):
                    print(f"   ⚠️  Error deleting jobs: {e}")
            
            # Then delete files that reference users
            try:
                cur.execute("DELETE FROM files")
                print(f"   ✅ Deleted {cur.rowcount} files")
            except Exception as e:
                if "does not exist" not in str(e):
                    print(f"   ⚠️  Error deleting files: {e}")
            
            # Delete password resets
            try:
                cur.execute("DELETE FROM password_resets")
                print(f"   ✅ Deleted {cur.rowcount} password resets")
            except Exception as e:
                if "does not exist" not in str(e):
                    print(f"   ⚠️  Error deleting password_resets: {e}")
            
            # Finally delete users
            cur.execute("DELETE FROM users")
            print(f"   ✅ Deleted {cur.rowcount} users")
        
        print("\n🎯 Database is now empty and ready for fresh signups")
        
    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        print("\nMake sure the database connection is valid.")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()