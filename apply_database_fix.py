#!/usr/bin/env python3
"""
Apply database fix for agent_workflows table
This script can be run within Railway environment
"""

import os
import psycopg2
from psycopg2 import sql

def apply_fix():
    # Get database URL from environment or use the provided one
    database_url = os.environ.get('DATABASE_URL', 
                                  'postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@postgres-rlai.railway.internal:5432/railway')
    
    print("Connecting to database...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("Connected successfully!")
        
        # Check current state
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agent_workflows' 
            AND column_name = 'institution_id';
        """)
        
        result = cur.fetchone()
        if result:
            print(f"Current institution_id type: {result[1]}")
        
        # Apply the fix
        print("\nApplying fix...")
        
        # Drop the existing foreign key constraint if it exists
        print("1. Dropping existing foreign key constraint...")
        cur.execute("""
            ALTER TABLE agent_workflows 
            DROP CONSTRAINT IF EXISTS agent_workflows_institution_id_fkey;
        """)
        
        # Alter the column type to match institutions.id
        print("2. Altering column type to VARCHAR(36)...")
        cur.execute("""
            ALTER TABLE agent_workflows 
            ALTER COLUMN institution_id TYPE VARCHAR(36);
        """)
        
        # Re-add the foreign key constraint
        print("3. Re-adding foreign key constraint...")
        cur.execute("""
            ALTER TABLE agent_workflows 
            ADD CONSTRAINT agent_workflows_institution_id_fkey 
            FOREIGN KEY (institution_id) REFERENCES institutions(id);
        """)
        
        # Commit the changes
        conn.commit()
        print("\n✅ Fix applied successfully!")
        
        # Verify the fix
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agent_workflows' 
            AND column_name = 'institution_id';
        """)
        
        result = cur.fetchone()
        if result:
            print(f"New institution_id type: {result[1]}")
        
        # Close connections
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False
    
    return True

if __name__ == "__main__":
    apply_fix()
