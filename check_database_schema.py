#!/usr/bin/env python3
"""
Check if the PostgreSQL database has all required tables.
Lists all tables and their columns to verify schema completeness.
"""

import psycopg2
from psycopg2 import sql
import json

def main():
    """Check database schema."""
    # Connection string for Railway PostgreSQL
    conn_string = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"
    
    try:
        conn = psycopg2.connect(conn_string)
        print("✅ Connected to Railway PostgreSQL database")
        print("=" * 70)
        
        with conn.cursor() as cur:
            # Get all tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            print(f"\n📊 Total tables in database: {len(tables)}")
            print("\n📋 Tables and their columns:")
            print("-" * 70)
            
            # For each table, get its columns
            for (table_name,) in tables:
                cur.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cur.fetchall()
                
                print(f"\n🗂️  Table: {table_name}")
                print("   Columns:")
                for col_name, data_type, nullable, default in columns:
                    nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    default_str = f" DEFAULT {default}" if default else ""
                    print(f"     - {col_name}: {data_type} {nullable_str}{default_str}")
            
            # Check for critical tables
            print("\n" + "=" * 70)
            print("🔍 Critical Tables Check:")
            print("-" * 70)
            
            critical_tables = [
                'users',
                'files', 
                'jobs',
                'teams',
                'sessions',
                'password_resets',
                'institutions',
                'standards',
                'evidence',
                'agent_workflows',
                'gap_analyses'
            ]
            
            table_names = [t[0] for t in tables]
            
            for table in critical_tables:
                if table in table_names:
                    print(f"✅ {table:<20} - EXISTS")
                else:
                    print(f"❌ {table:<20} - MISSING")
            
            # Check for any indexes
            print("\n📈 Indexes:")
            print("-" * 70)
            cur.execute("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            indexes = cur.fetchall()
            
            if indexes:
                current_table = None
                for table, idx_name, idx_def in indexes:
                    if table != current_table:
                        print(f"\n   Table: {table}")
                        current_table = table
                    print(f"     - {idx_name}")
            else:
                print("   No indexes found")
            
            # Check for foreign key constraints
            print("\n🔗 Foreign Key Constraints:")
            print("-" * 70)
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name
            """)
            
            fks = cur.fetchall()
            if fks:
                for table, column, ref_table, ref_column in fks:
                    print(f"   {table}.{column} -> {ref_table}.{ref_column}")
            else:
                print("   No foreign keys found")
                
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        return
    finally:
        if 'conn' in locals():
            conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Schema check complete!")


if __name__ == "__main__":
    main()