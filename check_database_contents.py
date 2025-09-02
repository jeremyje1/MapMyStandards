#!/usr/bin/env python3
"""
Check Railway PostgreSQL database contents
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import json
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv('railway.env')
load_dotenv('.env')

def check_database():
    """Check database tables and content"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print("🔍 Connecting to Railway PostgreSQL database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("✅ Connected successfully!\n")
        
        # 1. Check what tables exist
        print("📊 EXISTING TABLES:")
        print("-" * 50)
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        if tables:
            for table in tables:
                table_name = table[0]
                # Get row count
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cur.fetchone()[0]
                print(f"  • {table_name}: {count} rows")
        else:
            print("  No tables found!")
        
        print("\n")
        
        # 2. Check for users table
        print("👥 USERS TABLE:")
        print("-" * 50)
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        if columns:
            print("  Columns:")
            for col in columns:
                print(f"    - {col[0]}: {col[1]}")
                
            # Sample data
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"\n  Total users: {user_count}")
        else:
            print("  ❌ Users table not found")
        
        print("\n")
        
        # 3. Check for accreditors table
        print("🏛️ ACCREDITORS TABLE:")
        print("-" * 50)
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'accreditors'
        """)
        if cur.fetchone()[0] > 0:
            cur.execute("SELECT accreditor_id, name, acronym FROM accreditors")
            accreditors = cur.fetchall()
            if accreditors:
                for acc in accreditors:
                    print(f"  • {acc[2]}: {acc[1]}")
            else:
                print("  ⚠️ Table exists but is empty")
        else:
            print("  ❌ Accreditors table not found")
        
        print("\n")
        
        # 4. Check for standards table
        print("📋 STANDARDS TABLE:")
        print("-" * 50)
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'standards'
        """)
        if cur.fetchone()[0] > 0:
            # Count standards by accreditor
            cur.execute("""
                SELECT a.acronym, COUNT(s.standard_id) 
                FROM standards s
                LEFT JOIN accreditors a ON s.accreditor_id = a.accreditor_id
                GROUP BY a.acronym
            """)
            standards_count = cur.fetchall()
            if standards_count and standards_count[0][1] > 0:
                for acc, count in standards_count:
                    print(f"  • {acc or 'Unknown'}: {count} standards")
            else:
                print("  ⚠️ Table exists but is empty")
                print("\n  Need to seed standards data!")
        else:
            print("  ❌ Standards table not found")
        
        print("\n")
        
        # 5. Check for documents/files tables
        print("📄 DOCUMENT TABLES:")
        print("-" * 50)
        for table_name in ['documents', 'files', 'uploads', 'evidence']:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = %s
            """, (table_name,))
            if cur.fetchone()[0] > 0:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cur.fetchone()[0]
                print(f"  • {table_name}: {count} documents")
        
        print("\n")
        
        # 6. Check for other important tables
        print("🔧 OTHER TABLES:")
        print("-" * 50)
        important_tables = ['institutions', 'compliance_checks', 'gap_analysis', 'reports', 'evidence_mappings']
        for table_name in important_tables:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = %s
            """, (table_name,))
            if cur.fetchone()[0] > 0:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cur.fetchone()[0]
                print(f"  • {table_name}: {count} rows")
        
        print("\n" + "=" * 50)
        print("📊 DATABASE SUMMARY:")
        print("=" * 50)
        
        # Summary
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        total_tables = cur.fetchone()[0]
        
        print(f"Total tables: {total_tables}")
        
        # Check if we need to seed data
        needs_seeding = []
        
        # Check accreditors
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'accreditors'")
        if cur.fetchone()[0] > 0:
            cur.execute("SELECT COUNT(*) FROM accreditors")
            if cur.fetchone()[0] == 0:
                needs_seeding.append("accreditors")
        else:
            needs_seeding.append("accreditors (table missing)")
        
        # Check standards
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'standards'")
        if cur.fetchone()[0] > 0:
            cur.execute("SELECT COUNT(*) FROM standards")
            if cur.fetchone()[0] == 0:
                needs_seeding.append("standards")
        else:
            needs_seeding.append("standards (table missing)")
        
        if needs_seeding:
            print("\n⚠️ NEEDS SEEDING:")
            for item in needs_seeding:
                print(f"  • {item}")
            print("\n💡 Run: python scripts/seed_sacscoc_standards.py")
        else:
            print("\n✅ Database is properly seeded with accreditation data!")
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to database: {e}")
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()