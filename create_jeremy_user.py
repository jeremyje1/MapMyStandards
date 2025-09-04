#!/usr/bin/env python3
"""
Create Jeremy's user account directly via Railway CLI
"""
import subprocess
import json

# Create the SQL command to insert the user
sql_command = """
INSERT INTO users (
    id, 
    email, 
    name, 
    password_hash,
    institution_name,
    institution_type,
    role,
    is_trial,
    trial_started_at,
    trial_ends_at,
    subscription_tier,
    stripe_customer_id,
    stripe_subscription_id,
    api_key,
    api_key_created_at,
    is_active,
    is_verified,
    email_verified_at,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid()::text,
    'jeremy.estrella@gmail.com',
    'Jeremy Estrella',
    'pending_reset',
    'Test Institution',
    'college',
    'Administrator',
    true,
    NOW(),
    NOW() + INTERVAL '7 days',
    'professional',
    'stripe_customer_id_pending',
    'stripe_subscription_id_pending',
    'a3e_' || encode(gen_random_bytes(32), 'base64'),
    NOW(),
    true,
    true,
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    is_active = true,
    is_verified = true,
    email_verified_at = NOW(),
    updated_at = NOW()
RETURNING id, email, api_key;
"""

print("Creating user account for jeremy.estrella@gmail.com...")
print("\nRun this command to create the user:")
print("\nrailway run psql $DATABASE_URL -c \"" + sql_command.replace('\n', ' ').replace('  ', ' ') + "\"")
print("\nOr connect to Railway database and run the SQL directly.")
print("\nAfter user is created, use 'Forgot Password' to set a password.")
