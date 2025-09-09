-- Migration: Add onboarding fields to users table (manual fallback)
-- Use if Alembic unavailable in production Railway environment.
-- Safe for Postgres and will NO-OP if columns already exist.

DO $$
BEGIN
    -- Add onboarding_completed if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='onboarding_completed'
    ) THEN
        ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
        UPDATE users SET onboarding_completed = FALSE WHERE onboarding_completed IS NULL;
    END IF;

    -- Add onboarding_data if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='onboarding_data'
    ) THEN
        ALTER TABLE users ADD COLUMN onboarding_data JSONB;
    END IF;
END $$;
