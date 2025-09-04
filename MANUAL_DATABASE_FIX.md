# Manual Database Fix Instructions

If you need to manually fix the agent_workflows table, run these SQL commands in the Railway PostgreSQL console:

## 1. Connect to Railway Database Console
Go to your Railway project dashboard and open the PostgreSQL database console.

## 2. Run These SQL Commands

```sql
-- Check current state
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'agent_workflows' 
AND column_name = 'institution_id';

-- Drop the existing foreign key constraint
ALTER TABLE agent_workflows 
DROP CONSTRAINT IF EXISTS agent_workflows_institution_id_fkey;

-- Alter the column type to match institutions.id
ALTER TABLE agent_workflows 
ALTER COLUMN institution_id TYPE VARCHAR(36);

-- Re-add the foreign key constraint
ALTER TABLE agent_workflows 
ADD CONSTRAINT agent_workflows_institution_id_fkey 
FOREIGN KEY (institution_id) REFERENCES institutions(id);

-- Verify the fix
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'agent_workflows' 
AND column_name = 'institution_id';
```

## 3. Expected Result
The `institution_id` column should now be of type `character varying(36)` instead of `uuid`.

## Alternative: Run Python Script
If you have access to run Python scripts in your Railway environment, you can also run:
```bash
python apply_database_fix.py
```

This will automatically apply all the fixes.
