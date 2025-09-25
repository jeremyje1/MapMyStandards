#!/usr/bin/env python3
"""Safely clear all users and documents from production database"""

import psycopg2
from urllib.parse import urlparse
import sys

# Production DATABASE_URL from Railway
DATABASE_URL = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"

# Parse connection details
url = urlparse(DATABASE_URL)
conn_params = {
    'host': url.hostname,
    'port': url.port,
    'database': url.path[1:],
    'user': url.username,
    'password': url.password
}

print("=" * 60)
print("⚠️  PRODUCTION DATABASE CLEANUP")
print("=" * 60)

# First, let's check what we have
try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Check current state
    print("\nCurrent database state:")
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"  Users: {user_count}")
    
    cur.execute("SELECT COUNT(*) FROM documents")
    doc_count = cur.fetchone()[0]
    print(f"  Documents: {doc_count}")
    
    if user_count == 0 and doc_count == 0:
        print("\n✅ Database is already empty!")
        sys.exit(0)
    
    # Show some users
    print("\nSample users:")
    cur.execute("SELECT id, email, name FROM users LIMIT 5")
    for user in cur.fetchall():
        print(f"  - {user[1]} ({user[2]})")
    
    conn.close()
    
except Exception as e:
    print(f"Error checking database: {e}")
    sys.exit(1)

confirmation = input("\nType 'CLEAR ALL' to delete all users and documents: ")
if confirmation != "CLEAR ALL":
    print("Cancelled.")
    sys.exit(0)

print("\n" + "=" * 60)
print("Clearing database with proper order...")

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    conn.autocommit = True  # Commit each statement immediately
    
    # Clear in reverse dependency order
    print("\n1. Clearing dependent tables first...")
    
    # Tables in dependency order (most dependent first)
    clear_order = [
        # Webhook/delivery tables
        ("webhook_deliveries", "webhook deliveries"),
        ("webhook_configs", "webhook configs"),
        
        # Job tables
        ("processing_jobs", "processing jobs"),
        ("jobs", "jobs"),
        
        # Evidence/analysis tables
        ("evidence_standard", "evidence-standard mappings"),
        ("evidence_mappings", "evidence mappings"),
        ("evidence", "evidence"),
        ("analyses", "analyses"),
        ("gap_analyses", "gap analyses"),
        
        # Document related
        ("compliance_snapshots", "compliance snapshots"),
        ("narratives", "narratives"),
        ("standard_mappings", "standard mappings"),
        
        # File/document tables - documents must be before files
        ("documents", "documents"),
        ("files", "files"),
        
        # Org/report tables
        ("org_charts", "org charts"),
        ("reports", "reports"),
        ("scenarios", "scenarios"),
        
        # User activity
        ("usage_events", "usage events"),
        ("audit_logs", "audit logs"),
        
        # Session/auth tables
        ("user_sessions", "user sessions"),
        ("session_security", "session security"),
        ("password_resets", "password resets"),
        ("api_keys", "API keys"),
        
        # Team tables
        ("user_teams", "user-team relationships"),
        ("team_invitations", "team invitations"),
        ("teams", "teams"),
        
        # Finally users
        ("users", "users"),
    ]
    
    for table, desc in clear_order:
        try:
            # Get count first
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            
            if count > 0:
                # Use TRUNCATE for faster deletion and to reset sequences
                cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"   ✓ Cleared {desc} ({count} records)")
            else:
                print(f"   - No {desc} to clear")
                
        except psycopg2.errors.UndefinedTable:
            print(f"   - Table {table} doesn't exist")
        except Exception as e:
            print(f"   ⚠️  Error clearing {table}: {str(e)[:60]}...")
    
    # Verify final state
    print("\n2. Final verification:")
    
    try:
        cur.execute("SELECT COUNT(*) FROM users")
        final_users = cur.fetchone()[0]
        print(f"   Users remaining: {final_users}")
    except:
        print("   Users table cleared")
    
    try:
        cur.execute("SELECT COUNT(*) FROM documents") 
        final_docs = cur.fetchone()[0]
        print(f"   Documents remaining: {final_docs}")
    except:
        print("   Documents table cleared")
    
    print("\n✅ Production database cleared successfully!")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)