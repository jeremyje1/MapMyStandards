-- Create webhook configuration table
CREATE TABLE IF NOT EXISTS webhook_configs (
    id VARCHAR(255) PRIMARY KEY,
    institution_id VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255),
    events JSONB NOT NULL,
    headers JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Retry configuration
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 60, -- seconds
    
    -- Statistics
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_error_at TIMESTAMP WITH TIME ZONE,
    last_error_message TEXT,
    total_sent INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    
    -- Indexes
    CONSTRAINT fk_webhook_institution FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);

CREATE INDEX idx_webhook_configs_institution ON webhook_configs(institution_id);
CREATE INDEX idx_webhook_configs_active ON webhook_configs(active);
CREATE INDEX idx_webhook_configs_events ON webhook_configs USING gin(events);

-- Create webhook delivery history table
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id VARCHAR(255) PRIMARY KEY,
    webhook_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    attempt_count INTEGER DEFAULT 0,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    
    -- Indexes
    CONSTRAINT fk_delivery_webhook FOREIGN KEY (webhook_id) REFERENCES webhook_configs(id) ON DELETE CASCADE
);

CREATE INDEX idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_event ON webhook_deliveries(event_type);
CREATE INDEX idx_webhook_deliveries_created ON webhook_deliveries(created_at DESC);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(response_status);

-- Sample webhook configurations for testing
-- INSERT INTO webhook_configs (id, institution_id, url, events, active) VALUES
-- ('wh_sample_1', 'inst_sample', 'https://webhook.site/test', '["evidence.uploaded", "evidence.processed"]', true);