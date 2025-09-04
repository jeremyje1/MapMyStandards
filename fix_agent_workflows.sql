
    -- Drop the existing foreign key constraint if it exists
    ALTER TABLE agent_workflows 
    DROP CONSTRAINT IF EXISTS agent_workflows_institution_id_fkey;
    
    -- Alter the column type to match institutions.id
    ALTER TABLE agent_workflows 
    ALTER COLUMN institution_id TYPE VARCHAR(36);
    
    -- Re-add the foreign key constraint
    ALTER TABLE agent_workflows 
    ADD CONSTRAINT agent_workflows_institution_id_fkey 
    FOREIGN KEY (institution_id) REFERENCES institutions(id);
    