#!/usr/bin/env python3
"""Clear all users and documents from production database"""

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
print("⚠️  WARNING: This will DELETE ALL DATA from PRODUCTION!")
print("=" * 60)
print("\nThis script will delete:")
print("- All users")
print("- All documents") 
print("- All related data (sessions, analyses, etc.)")
print("\nDatabase:", url.hostname)

confirmation = input("\nType 'DELETE EVERYTHING' to confirm: ")
if confirmation != "DELETE EVERYTHING":
    print("Cancelled.")
    sys.exit(0)

print("\n" + "=" * 60)
print("Clearing production database...")

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Start transaction
    conn.autocommit = False
    
    print("\n1. Clearing document-related tables...")
    tables_to_clear = [
        # Document related
        ('evidence_standard', 'evidence-standard mappings'),
        ('evidence_mappings', 'evidence mappings'),
        ('evidence', 'evidence records'),
        ('analyses', 'analyses'),
        ('gap_analyses', 'gap analyses'),
        ('files', 'file records'),
        ('documents', 'documents'),
        
        # User activity related
        ('compliance_snapshots', 'compliance snapshots'),
        ('narratives', 'narratives'),
        ('org_charts', 'org charts'),
        ('reports', 'reports'),
        ('scenarios', 'scenarios'),
        ('standard_mappings', 'standard mappings'),
        
        # Session/auth related
        ('user_sessions', 'user sessions'),
        ('session_security', 'session security'),
        ('password_resets', 'password resets'),
        ('api_keys', 'API keys'),
        
        # Team related
        ('user_teams', 'user-team relationships'),
        ('team_invitations', 'team invitations'),
        ('teams', 'teams'),
        
        # Job/webhook related
        ('webhook_deliveries', 'webhook deliveries'),
        ('webhook_configs', 'webhook configs'),
        ('processing_jobs', 'processing jobs'),
        ('jobs', 'jobs'),
        
        # Usage tracking
        ('usage_events', 'usage events'),
        ('audit_logs', 'audit logs'),
        
        # Finally, users
        ('users', 'users'),
    ]
    
    for table, description in tables_to_clear:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count > 0:
                cur.execute(f"DELETE FROM {table}")
                print(f"   ✓ Deleted {count} {description}")
            else:
                print(f"   - No {description} to delete")
        except Exception as e:
            print(f"   ⚠️  Skipping {table}: {str(e)[:50]}...")
    
    # Don't delete system tables
    print("\n2. Preserving system tables:")
    system_tables = [
        'accreditation_standards',
        'accreditors', 
        'standards',
        'institutions',
        'institution_accreditor',
        'alembic_version',
        'database_health_check',
        'system_metrics',
        'powerbi_configs',
        'agent_workflows'
    ]
    
    for table in system_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"   - Keeping {count} records in {table}")
        except:
            pass
    
    # Commit changes
    conn.commit()
    print("\n✅ Production database cleared successfully!")
    
    # Show final state
    print("\n3. Final user count:")
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"   Users remaining: {user_count}")
    
    cur.execute("SELECT COUNT(*) FROM documents")
    doc_count = cur.fetchone()[0]
    print(f"   Documents remaining: {doc_count}")
    
    conn.close()
    
except Exception as e:
    if conn:
        conn.rollback()
    print(f"\n❌ Error: {e}")
    print("Transaction rolled back - no changes made.")

print("\n" + "=" * 60)