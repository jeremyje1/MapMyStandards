-- Migration: Add authentication fields to users table
-- Date: 2025-09-01
-- Description: Add missing authentication and subscription fields to match the User model

BEGIN;

-- Add authentication fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Add organization info fields  
ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_type VARCHAR(50);

-- Add trial and subscription info
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);

-- Add API access fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_created_at TIMESTAMP;

-- Add additional account status fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

-- Add usage tracking fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS documents_analyzed INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reports_generated INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS compliance_checks_run INTEGER DEFAULT 0;

-- Add unique indexes for important fields
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key) WHERE api_key IS NOT NULL;

-- Update existing users to have proper defaults
UPDATE users SET 
    is_trial = TRUE,
    trial_started_at = COALESCE(created_at, NOW()),
    is_verified = FALSE,
    documents_analyzed = 0,
    reports_generated = 0,
    compliance_checks_run = 0
WHERE is_trial IS NULL;

COMMIT;

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
    AND table_schema = 'public'
ORDER BY ordinal_position;