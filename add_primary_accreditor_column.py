#!/usr/bin/env python3
"""
Add primary_accreditor column to users table
"""
import os
from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.exc import ProgrammingError

def add_primary_accreditor_column():
    """Add primary_accreditor column if it doesn't exist"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
        
    print(f"📊 Connecting to database...")
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'primary_accreditor'
            """))
            
            if result.fetchone():
                print("✅ primary_accreditor column already exists")
                return True
            
            # Add the column
            print("🔨 Adding primary_accreditor column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN primary_accreditor VARCHAR(255)
            """))
            conn.commit()
            print("✅ primary_accreditor column added successfully")
            
            # Also add department column if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'department'
            """))
            
            if not result.fetchone():
                print("🔨 Adding department column...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN department VARCHAR(255)
                """))
                conn.commit()
                print("✅ department column added successfully")
            
            return True
            
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column already exists")
            return True
        else:
            print(f"❌ Error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Adding primary_accreditor column to users table\n")
    
    if add_primary_accreditor_column():
        print("\n✨ Database schema updated!")
        print("The primary_accreditor field will now be saved directly to the database.")
    else:
        print("\n❌ Failed to update database schema")