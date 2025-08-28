#!/usr/bin/env python3
"""
Clear test accounts from the database
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.a3e.database.connection import db_manager
from src.a3e.database.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def clear_test_accounts():
    """Clear all test accounts from the database"""
    try:
        # Try to initialize database manager
        try:
            await db_manager.initialize()
            print("✅ Database manager initialized")
        except Exception as e:
            print(f"⚠️ Database manager init failed: {e}")
            # Fallback to direct connection
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                # Use SQLite fallback for local
                database_url = "sqlite:///a3e_production.db"
            
            if database_url.startswith('postgresql'):
                # Use sync postgresql driver
                database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            
            print(f"Using direct connection to: {database_url}")
            engine = create_engine(database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
        
        # If database manager worked, use async session
        if db_manager._initialized:
            async with db_manager.get_session() as session:
                users = await session.execute("SELECT * FROM users")
                users = users.fetchall()
                print(f"Found {len(users)} total users in database")
                
                if users:
                    print("\nUsers to be deleted:")
                    for user in users:
                        print(f"  - {user.email} (ID: {user.id})")
                    
                    confirm = input(f"\nDo you want to delete all {len(users)} users? (yes/no): ")
                    if confirm.lower() in ['yes', 'y']:
                        await session.execute("DELETE FROM users")
                        await session.commit()
                        print(f"✅ Successfully deleted all users")
                    else:
                        print("❌ Operation cancelled")
        else:
            # Use sync session fallback
            users = session.query(User).all()
            print(f"Found {len(users)} total users in database")
            
            if not users:
                print("No users found in database")
                session.close()
                return
            
            # Show users before deletion
            print("\nUsers to be deleted:")
            for user in users:
                print(f"  - {user.email} (ID: {user.id}, Created: {user.created_at})")
            
            # Confirm deletion
            confirm = input(f"\nDo you want to delete all {len(users)} users? (yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                # Delete all users
                deleted_count = session.query(User).delete()
                session.commit()
                print(f"✅ Successfully deleted {deleted_count} users")
            else:
                print("❌ Operation cancelled")
            
            session.close()
        
    except Exception as e:
        print(f"❌ Error clearing test accounts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_test_accounts())