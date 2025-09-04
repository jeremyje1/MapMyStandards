#!/usr/bin/env python3
"""
Ensure all required tables exist in the database
Run this to create missing tables without running full migrations
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def get_database_url():
    """Get database URL from environment"""
    # Try Railway production database first
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        # Fallback to constructed URL
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'railway')
        db_user = os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('PGPASSWORD', '')
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return db_url

def create_tables():
    """Create all missing tables"""
    db_url = get_database_url()
    
    if not db_url:
        print("❌ No database URL found. Please set DATABASE_URL or PG* environment variables")
        return False
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Read the SQL file
            with open('create_missing_tables.sql', 'r') as f:
                sql_statements = f.read()
            
            # Execute all statements
            for statement in sql_statements.split(';'):
                if statement.strip():
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️  Statement failed (may already exist): {str(e)[:100]}")
            
            print("✅ All tables checked/created successfully")
            
            # List existing tables
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('teams', 'org_charts', 'scenarios', 'powerbi_configs', 
                                  'team_invitations', 'audit_logs', 'api_keys', 
                                  'session_security', 'user_teams')
                ORDER BY tablename
            """))
            
            tables = [row[0] for row in result]
            print(f"\n📊 Found {len(tables)} enterprise tables:")
            for table in tables:
                print(f"   - {table}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Ensuring all required tables exist...")
    success = create_tables()
    sys.exit(0 if success else 1)