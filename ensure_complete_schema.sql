-- Comprehensive schema verification and creation script
-- Run this to ensure all tables and relationships are properly set up

-- Check and create any missing tables
DO $$
BEGIN
    -- Ensure all core tables exist with correct structure
    
    -- Users table (should already exist)
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE TABLE users (
            id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255),
            role VARCHAR(50),
            institution_id VARCHAR(36),
            auth_provider VARCHAR(20),
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    END IF;

    -- Ensure all foreign key constraints exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'files_user_id_fkey'
    ) THEN
        ALTER TABLE files 
        ADD CONSTRAINT files_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'jobs_user_id_fkey'
    ) THEN
        ALTER TABLE jobs 
        ADD CONSTRAINT jobs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'jobs_file_id_fkey'
    ) THEN
        ALTER TABLE jobs 
        ADD CONSTRAINT jobs_file_id_fkey 
        FOREIGN KEY (file_id) REFERENCES files(file_id);
    END IF;

END $$;

-- Verify all tables have proper indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_institution ON users(institution_id);
CREATE INDEX IF NOT EXISTS idx_institutions_name ON institutions(name);
CREATE INDEX IF NOT EXISTS idx_accreditors_acronym ON accreditors(acronym);
CREATE INDEX IF NOT EXISTS idx_standards_accreditor ON standards(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_files_user ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_teams_slug ON teams(slug);

-- Add any missing columns to existing tables
DO $$
BEGIN
    -- Add missing columns to users table if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'password_hash') THEN
        ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'is_trial') THEN
        ALTER TABLE users ADD COLUMN is_trial BOOLEAN DEFAULT true;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'trial_ends_at') THEN
        ALTER TABLE users ADD COLUMN trial_ends_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'stripe_customer_id') THEN
        ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'subscription_status') THEN
        ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50);
    END IF;
END $$;

-- Create a summary view of the database state
CREATE OR REPLACE VIEW database_health_check AS
SELECT 
    'Tables' as check_type,
    COUNT(*) as count,
    string_agg(tablename, ', ' ORDER BY tablename) as items
FROM pg_tables 
WHERE schemaname = 'public'
UNION ALL
SELECT 
    'Indexes' as check_type,
    COUNT(*) as count,
    string_agg(indexname, ', ' ORDER BY indexname) as items
FROM pg_indexes 
WHERE schemaname = 'public'
UNION ALL
SELECT 
    'Foreign Keys' as check_type,
    COUNT(*) as count,
    string_agg(constraint_name, ', ' ORDER BY constraint_name) as items
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY' AND constraint_schema = 'public';

-- Display the health check
SELECT * FROM database_health_check;