#!/usr/bin/env python3
"""
Clear all users from the Railway PostgreSQL database
WARNING: This will delete ALL user data!
"""

import psycopg2
import sys

def clear_all_users():
    try:
        # Direct connection string
        conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
        
        print("⚠️  WARNING: This will DELETE ALL USERS from the database!")
        print("=" * 60)
        
        # First, let's check current users
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        
        print(f"\n📊 Current user count: {count}")
        
        if count > 0:
            cur.execute("SELECT email, institution_name FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
            print("\n👥 Users to be deleted:")
            for user in users:
                print(f"   - {user[0]} ({user[1] if user[1] else 'No institution'})")
        
        print("\n⚠️  Are you sure you want to delete all users? Type 'DELETE ALL' to confirm:")
        confirmation = input().strip()
        
        if confirmation != "DELETE ALL":
            print("❌ Cancelled. No users were deleted.")
            cur.close()
            conn.close()
            return
        
        # Delete all users and related data
        print("\n🗑️  Deleting all users and related data...")
        
        # Delete in proper order to respect foreign key constraints
        jobs_deleted = 0
        files_deleted = 0
        sessions_deleted = 0
        teams_deleted = 0
        
        try:
            print("   - Deleting jobs...")
            cur.execute("DELETE FROM jobs WHERE file_id IN (SELECT file_id FROM files WHERE user_id IN (SELECT id FROM users))")
            jobs_deleted = cur.rowcount
        except Exception as e:
            if "does not exist" not in str(e):
                raise
        
        try:
            print("   - Deleting user files...")
            cur.execute("DELETE FROM files WHERE user_id IN (SELECT id FROM users)")
            files_deleted = cur.rowcount
        except Exception as e:
            if "does not exist" not in str(e):
                raise
        
        try:
            print("   - Deleting user sessions...")
            cur.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users)")
            sessions_deleted = cur.rowcount
        except Exception as e:
            if "does not exist" not in str(e):
                raise
        
        try:
            print("   - Deleting user teams...")
            cur.execute("DELETE FROM teams WHERE user_id IN (SELECT id FROM users)")
            teams_deleted = cur.rowcount
        except Exception as e:
            if "does not exist" not in str(e):
                raise
        
        print("   - Deleting users...")
        cur.execute("DELETE FROM users")
        deleted_count = cur.rowcount
        
        # Commit the changes
        conn.commit()
        
        # Verify deletion
        cur.execute("SELECT COUNT(*) FROM users")
        new_count = cur.fetchone()[0]
        
        print(f"\n✅ Successfully deleted:")
        print(f"   - {deleted_count} users")
        print(f"   - {files_deleted} files")
        print(f"   - {sessions_deleted} sessions")
        print(f"   - {teams_deleted} teams")
        print(f"   - {jobs_deleted} jobs")
        print(f"\n📊 Remaining users: {new_count}")
        
        # Also clear any related tables if needed
        print("\n🧹 Cleaning up related data...")
        
        # Clear password_resets if table exists
        try:
            cur.execute("DELETE FROM password_resets")
            conn.commit()
            print("   ✅ Cleared password_resets table")
        except:
            print("   ℹ️  No password_resets table or already empty")
        
        # Clear user_settings if exists
        try:
            cur.execute("DELETE FROM user_settings")
            conn.commit()
            print("   ✅ Cleared user_settings table")
        except:
            print("   ℹ️  No user_settings table or already empty")
        
        cur.close()
        conn.close()
        
        print("\n✅ Database cleanup complete!")
        print("\n📝 Next steps:")
        print("1. The Stripe webhook will create users automatically when checkout completes")
        print("2. We need to fix the onboarding to update the database with institution data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure the database connection is valid.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        # Skip confirmation for automation
        clear_all_users()
    else:
        print("🗑️  Clear All Users Tool")
        print("=" * 60)
        print("\nThis tool will permanently delete ALL users from the database.")
        print("This action cannot be undone!")
        print("\nTo proceed, run:")
        print("  python3 clear_all_users.py")
        print("\nYou will be asked to confirm before any deletions occur.")
        clear_all_users()

if __name__ == "__main__":
    main()