#!/usr/bin/env python3
"""
Clear test user data from the database for continued testing.
This script safely removes all user data and related records.
"""

import os
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from a3e.services.database_service import DatabaseService
from a3e.core.config import get_settings

async def clear_test_users():
    """Clear all test user data from the database"""
    settings = get_settings()
    db_service = DatabaseService(settings.database_url)
    
    async with db_service.get_session() as session:
        try:
            print("🧹 Starting database cleanup...")
            
            # Delete in order to respect foreign key constraints
            # 1. Usage events (references users)
            result = await session.execute(text("DELETE FROM usage_events"))
            usage_deleted = result.rowcount
            print(f"   ✓ Deleted {usage_deleted} usage events")
            
            # 2. Password resets (references users)
            result = await session.execute(text("DELETE FROM password_resets"))
            resets_deleted = result.rowcount
            print(f"   ✓ Deleted {resets_deleted} password resets")
            
            # 3. User sessions (references users)
            result = await session.execute(text("DELETE FROM user_sessions"))
            sessions_deleted = result.rowcount
            print(f"   ✓ Deleted {sessions_deleted} user sessions")
            
            # 4. Users (main table)
            result = await session.execute(text("DELETE FROM users"))
            users_deleted = result.rowcount
            print(f"   ✓ Deleted {users_deleted} users")
            
            await session.commit()
            
            print(f"\n✅ Database cleanup completed successfully!")
            print(f"   • Total users removed: {users_deleted}")
            print(f"   • Total sessions removed: {sessions_deleted}")
            print(f"   • Total usage events removed: {usage_deleted}")
            print(f"   • Total password resets removed: {resets_deleted}")
            print("\n🔄 You can now continue testing with fresh user accounts")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("🗑️  A³E Database User Cleanup Tool")
    print("=" * 50)
    
    # Check for --force flag or interactive confirmation
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("⚡ Force mode enabled - proceeding with cleanup...")
        asyncio.run(clear_test_users())
    else:
        # Interactive mode
        try:
            confirm = input("\n⚠️  This will permanently DELETE ALL user data from the database.\n   Type 'YES' to proceed: ")
            
            if confirm != "YES":
                print("❌ Operation cancelled.")
                sys.exit(0)
            
            asyncio.run(clear_test_users())
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operation cancelled.")
            sys.exit(0)