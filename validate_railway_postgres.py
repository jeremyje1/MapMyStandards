#!/usr/bin/env python3
"""
Railway PostgreSQL Configuration Validation

This script validates that the Railway PostgreSQL database configuration
is working properly with all recent updates.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def validate_railway_postgres():
    """Validate Railway PostgreSQL configuration"""
    
    print("🚂 Railway PostgreSQL Configuration Validation")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. 🔍 Environment Variables Check:")
    print("-" * 35)
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Mask the password for security
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                masked_url = f"{user_pass[0]}:***@{parts[1]}"
            else:
                masked_url = f"{parts[0]}:***@{parts[1]}"
        else:
            masked_url = database_url[:20] + "..."
        
        print(f"✅ DATABASE_URL: {masked_url}")
        
        if database_url.startswith('postgresql://'):
            print("✅ Database Type: PostgreSQL (Railway)")
        elif database_url.startswith('sqlite:'):
            print("⚠️  Database Type: SQLite (Local Development)")
        else:
            print(f"❓ Database Type: Unknown ({database_url[:10]}...)")
    else:
        print("❌ DATABASE_URL: Not set")
        return False
    
    # Check database connection
    print("\n2. 🔌 Database Connection Test:")
    print("-" * 35)
    
    try:
        from a3e.database.connection import db_manager
        
        # Initialize the database manager
        await db_manager.initialize()
        print("✅ Database manager initialized successfully")
        
        # Test health check
        health_status = await db_manager.health_check()
        if health_status:
            print("✅ Database health check passed")
        else:
            print("❌ Database health check failed")
            return False
            
        # Get database metrics
        try:
            metrics = await db_manager.get_metrics()
            print(f"✅ Database metrics retrieved:")
            print(f"   - Connection Pool: {metrics.get('pool_status', 'Unknown')}")
            print(f"   - Active Connections: {metrics.get('active_connections', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Could not retrieve metrics: {e}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check if tables exist
    print("\n3. 📊 Database Schema Check:")
    print("-" * 35)
    
    try:
        async with db_manager.get_session() as session:
            # Check for key tables
            tables_to_check = [
                'users', 'institutions', 'accreditation_standards',
                'documents', 'reports', 'api_keys'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                try:
                    result = await session.execute(f"SELECT 1 FROM {table} LIMIT 1")
                    existing_tables.append(table)
                except:
                    pass
            
            if existing_tables:
                print(f"✅ Found {len(existing_tables)} tables:")
                for table in existing_tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No tables found - database may need initialization")
                
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False
    
    # Check enterprise features
    print("\n4. 🏢 Enterprise Features Check:")
    print("-" * 35)
    
    try:
        async with db_manager.get_session() as session:
            # Check enterprise tables
            enterprise_tables = ['teams', 'team_invitations', 'audit_logs']
            
            enterprise_ready = []
            for table in enterprise_tables:
                try:
                    result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    enterprise_ready.append((table, count))
                except:
                    pass
            
            if enterprise_ready:
                print("✅ Enterprise features database ready:")
                for table, count in enterprise_ready:
                    print(f"   - {table}: {count} records")
            else:
                print("⚠️  Enterprise tables not found")
                
    except Exception as e:
        print(f"⚠️  Enterprise check failed: {e}")
    
    # Check email service integration
    print("\n5. 📧 Email Service Integration:")
    print("-" * 35)
    
    try:
        from a3e.services.email_service_postmark import get_email_service
        
        email_service = get_email_service()
        if email_service.provider:
            print(f"✅ Email service configured: {email_service.provider}")
            print(f"✅ From email: {email_service.from_email}")
            print(f"✅ Admin email: {email_service.admin_email}")
        else:
            print("❌ Email service not configured")
            
    except Exception as e:
        print(f"❌ Email service check failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Railway PostgreSQL validation completed!")
    
    return True

if __name__ == "__main__":
    import asyncio
    
    try:
        result = asyncio.run(validate_railway_postgres())
        if result:
            print("✅ All systems operational!")
            sys.exit(0)
        else:
            print("❌ Issues found - check configuration")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
