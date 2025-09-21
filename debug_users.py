#!/usr/bin/env python3
import psycopg2

def main():
    """Debug user table contents."""
    conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
    conn = psycopg2.connect(conn_string)
    
    with conn.cursor() as cur:
        # Check how many rows are in users table
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        print(f"Total users in database: {count}")
        
        # If there are users, show their details
        if count > 0:
            cur.execute("SELECT id, email, created_at FROM users")
            users = cur.fetchall()
            print("\nUsers found:")
            for user_id, email, created_at in users:
                print(f"  - {user_id}: {email} (created: {created_at})")

if __name__ == "__main__":
    main()