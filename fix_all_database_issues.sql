-- Comprehensive database fix for all foreign key issues

-- Fix files table if it references wrong column
DROP TABLE IF EXISTS files CASCADE;
CREATE TABLE IF NOT EXISTS files (
    file_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id), -- Reference correct column
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    content_type VARCHAR(100),
    file_size BIGINT,
    file_content BYTEA,
    title VARCHAR(255),
    description TEXT,
    accreditor_id VARCHAR REFERENCES accreditors(accreditor_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix jobs table if needed
DROP TABLE IF EXISTS jobs CASCADE;
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    file_id VARCHAR(36) REFERENCES files(file_id),
    status VARCHAR(50),
    progress INTEGER DEFAULT 0,
    description TEXT,
    error_message TEXT,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create standard_mappings table if missing (referenced in services)
CREATE TABLE IF NOT EXISTS standard_mappings (
    id VARCHAR(36) PRIMARY KEY,
    institution_id VARCHAR(36) REFERENCES institutions(id),
    standard_id VARCHAR REFERENCES standards(standard_id),
    evidence_id VARCHAR(36) REFERENCES evidence(id),
    mapping_status VARCHAR(50),
    confidence_score FLOAT,
    notes TEXT,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create reports table if missing
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) PRIMARY KEY,
    institution_id VARCHAR(36) REFERENCES institutions(id),
    report_type VARCHAR(50),
    status VARCHAR(50),
    file_path VARCHAR(500),
    generated_by VARCHAR(36) REFERENCES users(id),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system_metrics table if missing  
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50),
    metric_value FLOAT,
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix any other association tables that might have issues
DROP TABLE IF EXISTS institution_accreditor CASCADE;
CREATE TABLE IF NOT EXISTS institution_accreditor (
    institution_id VARCHAR(36) REFERENCES institutions(id),
    accreditor_id VARCHAR REFERENCES accreditors(accreditor_id),
    PRIMARY KEY (institution_id, accreditor_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_file_id ON jobs(file_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_standard_mappings_institution ON standard_mappings(institution_id);
CREATE INDEX IF NOT EXISTS idx_reports_institution ON reports(institution_id);