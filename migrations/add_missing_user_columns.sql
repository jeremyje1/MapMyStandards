-- Add missing columns to users table
-- Run this in Railway PostgreSQL database

-- Add onboarding columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_data JSONB DEFAULT '{}'::jsonb;

-- Add usage tracking columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS documents_analyzed INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reports_generated INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS compliance_checks_run INTEGER DEFAULT 0;

-- Add optional profile columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR;

-- Add authentication columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;

-- Add timestamp columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_created_at TIMESTAMP;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Verify columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;
