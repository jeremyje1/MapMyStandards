-- Create missing tables for OrgChart, Scenario, and PowerBIConfig
-- Run this directly on the Railway PostgreSQL database if needed

-- Create org_charts table
CREATE TABLE IF NOT EXISTS org_charts (
    id VARCHAR PRIMARY KEY,
    team_id VARCHAR REFERENCES teams(id),
    user_id VARCHAR REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    chart_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create scenarios table
CREATE TABLE IF NOT EXISTS scenarios (
    id VARCHAR PRIMARY KEY,
    team_id VARCHAR REFERENCES teams(id),
    user_id VARCHAR REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create powerbi_configs table
CREATE TABLE IF NOT EXISTS powerbi_configs (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    workspace_id VARCHAR,
    report_id VARCHAR,
    dataset_id VARCHAR,
    tenant_id VARCHAR,
    client_id VARCHAR,
    embed_token TEXT,
    embed_url TEXT,
    config_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create teams table if it doesn't exist
CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    max_users INTEGER DEFAULT 10,
    stripe_customer_id VARCHAR,
    subscription_tier VARCHAR DEFAULT 'starter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id VARCHAR REFERENCES users(id)
);

-- Create team_invitations table if it doesn't exist  
CREATE TABLE IF NOT EXISTS team_invitations (
    id VARCHAR PRIMARY KEY,
    team_id VARCHAR REFERENCES teams(id),
    email VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'viewer',
    token VARCHAR UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id VARCHAR REFERENCES users(id)
);

-- Create audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR PRIMARY KEY,
    team_id VARCHAR REFERENCES teams(id),
    user_id VARCHAR REFERENCES users(id),
    action VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id VARCHAR,
    details JSONB,
    ip_address VARCHAR,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create api_keys table if it doesn't exist
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR PRIMARY KEY,
    team_id VARCHAR REFERENCES teams(id),
    user_id VARCHAR REFERENCES users(id),
    name VARCHAR NOT NULL,
    key_hash VARCHAR UNIQUE NOT NULL,
    prefix VARCHAR NOT NULL,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    scopes JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create session_security table if it doesn't exist
CREATE TABLE IF NOT EXISTS session_security (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    session_token VARCHAR UNIQUE NOT NULL,
    ip_address VARCHAR,
    user_agent TEXT,
    device_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Create user_teams association table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_teams (
    user_id VARCHAR REFERENCES users(id),
    team_id VARCHAR REFERENCES teams(id),
    role VARCHAR NOT NULL DEFAULT 'viewer',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, team_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_org_charts_team_id ON org_charts(team_id);
CREATE INDEX IF NOT EXISTS idx_org_charts_user_id ON org_charts(user_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_team_id ON scenarios(team_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_user_id ON scenarios(user_id);
CREATE INDEX IF NOT EXISTS idx_powerbi_configs_user_id ON powerbi_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_teams_slug ON teams(slug);
CREATE INDEX IF NOT EXISTS idx_audit_logs_team_id ON audit_logs(team_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);