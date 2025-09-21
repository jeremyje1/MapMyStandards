#!/usr/bin/env python3
"""Create webhook tables in the database."""

import os
from sqlalchemy import create_engine, text

# Use the provided database URL - public URL (has egress costs)
DATABASE_URL = "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway"

print("🔄 Creating webhook tables...")

# Create engine
engine = create_engine(DATABASE_URL)

# SQL for creating webhook tables
create_webhook_tables_sql = """
-- Create webhook configs table
CREATE TABLE IF NOT EXISTS webhook_configs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    institution_id VARCHAR(36) NOT NULL,
    url TEXT NOT NULL,
    secret TEXT,
    events JSONB NOT NULL,
    headers JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 60,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_error_at TIMESTAMP WITH TIME ZONE,
    last_error_message TEXT,
    total_sent INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0
);

-- Create webhook deliveries table for tracking webhook calls
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    webhook_id VARCHAR(36) NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    attempt_count INTEGER DEFAULT 0,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_webhook_configs_institution_id ON webhook_configs(institution_id);
CREATE INDEX IF NOT EXISTS idx_webhook_configs_active ON webhook_configs(active);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_created_at ON webhook_deliveries(created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to webhook_configs
DROP TRIGGER IF EXISTS update_webhook_configs_updated_at ON webhook_configs;
CREATE TRIGGER update_webhook_configs_updated_at BEFORE UPDATE ON webhook_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

GRANT ALL ON webhook_configs TO postgres;
GRANT ALL ON webhook_deliveries TO postgres;
"""

try:
    with engine.connect() as conn:
        # Execute the SQL
        conn.execute(text(create_webhook_tables_sql))
        conn.commit()
        
        # Verify tables were created
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('webhook_configs', 'webhook_deliveries')
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        print("\n✅ Webhook tables created successfully!")
        print(f"   Tables created: {', '.join(tables)}")
        
        # Check if we can query the tables
        webhook_count = conn.execute(text("SELECT COUNT(*) FROM webhook_configs")).scalar()
        delivery_count = conn.execute(text("SELECT COUNT(*) FROM webhook_deliveries")).scalar()
        
        print(f"\n📊 Current data:")
        print(f"   - Webhook configs: {webhook_count}")
        print(f"   - Webhook deliveries: {delivery_count}")
        
except Exception as e:
    print(f"\n❌ Error creating webhook tables: {e}")
    raise