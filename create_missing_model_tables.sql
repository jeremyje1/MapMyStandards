-- Create missing tables for database models
-- These tables are referenced in the Python models but don't exist in the database

-- Create gap_analyses table
CREATE TABLE IF NOT EXISTS gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id VARCHAR(36) NOT NULL REFERENCES institutions(id),
    accreditor_id VARCHAR(20) NOT NULL,
    
    -- Analysis metadata
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    academic_year VARCHAR(10) NOT NULL,
    analyst_type VARCHAR(20) DEFAULT 'agent',
    
    -- Gap results
    total_standards INTEGER NOT NULL,
    standards_with_evidence INTEGER NOT NULL,
    standards_without_evidence INTEGER NOT NULL,
    standards_insufficient_evidence INTEGER NOT NULL,
    
    -- Detailed gap data
    gap_details JSONB NOT NULL,
    risk_assessment JSONB,
    recommendations JSONB,
    
    -- Quality metrics
    confidence_score FLOAT DEFAULT 0.0,
    completeness_score FLOAT DEFAULT 0.0,
    
    -- Status tracking
    is_current BOOLEAN DEFAULT TRUE,
    reviewed_by_human BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approval_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_gap_analysis_per_year UNIQUE (institution_id, accreditor_id, academic_year)
);

-- Create narratives table
CREATE TABLE IF NOT EXISTS narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id VARCHAR(36) NOT NULL REFERENCES institutions(id),
    standard_id VARCHAR(50) NOT NULL REFERENCES standards(standard_id),
    
    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB,
    
    -- Generation metadata
    generated_by VARCHAR(50) DEFAULT 'agent',
    llm_model VARCHAR(100),
    generation_config JSONB,
    
    -- Quality and review
    quality_score FLOAT DEFAULT 0.0,
    citation_accuracy FLOAT DEFAULT 0.0,
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_edited BOOLEAN DEFAULT FALSE,
    
    -- Version control
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    previous_version_id UUID REFERENCES narratives(id),
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    
    -- Actor information
    user_id VARCHAR(100),
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    change_summary VARCHAR(500),
    
    -- Context
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    session_id VARCHAR(100),
    
    -- Timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_audit_entity_time UNIQUE (entity_type, entity_id, timestamp)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_gap_analyses_institution ON gap_analyses(institution_id);
CREATE INDEX IF NOT EXISTS idx_gap_analyses_accreditor ON gap_analyses(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_narratives_institution ON narratives(institution_id);
CREATE INDEX IF NOT EXISTS idx_narratives_standard ON narratives(standard_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);