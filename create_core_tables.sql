-- Create core tables that are missing from the database
-- These are referenced by other tables but don't exist yet

-- Create institutions table
CREATE TABLE IF NOT EXISTS institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    institution_type VARCHAR,
    accreditor_id VARCHAR,
    description TEXT,
    address TEXT,
    website VARCHAR,
    contact_email VARCHAR,
    contact_phone VARCHAR,
    status VARCHAR DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create accreditors table  
CREATE TABLE IF NOT EXISTS accreditors (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    full_name VARCHAR,
    accreditor_type VARCHAR,
    description TEXT,
    website VARCHAR,
    contact_email VARCHAR,
    region VARCHAR,
    status VARCHAR DEFAULT 'active',
    recognition_status VARCHAR,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create standards table if missing
CREATE TABLE IF NOT EXISTS standards (
    id VARCHAR PRIMARY KEY,
    accreditor_id VARCHAR REFERENCES accreditors(id),
    code VARCHAR NOT NULL,
    category VARCHAR,
    subcategory VARCHAR,
    description TEXT,
    full_text TEXT,
    evidence_required TEXT,
    compliance_level VARCHAR,
    effective_date DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create evidence table if missing
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    title VARCHAR NOT NULL,
    description TEXT,
    file_path VARCHAR,
    file_type VARCHAR,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR,
    status VARCHAR DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the association tables
CREATE TABLE IF NOT EXISTS institution_accreditor (
    institution_id UUID REFERENCES institutions(id),
    accreditor_id VARCHAR REFERENCES accreditors(id),
    PRIMARY KEY (institution_id, accreditor_id)
);

CREATE TABLE IF NOT EXISTS evidence_standard (
    evidence_id UUID REFERENCES evidence(id),
    standard_id VARCHAR REFERENCES standards(id),
    confidence_score FLOAT DEFAULT 0.0,
    mapped_by_agent BOOLEAN DEFAULT TRUE,
    verified_by_human BOOLEAN DEFAULT FALSE,
    mapping_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (evidence_id, standard_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_institutions_accreditor ON institutions(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_standards_accreditor ON standards(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_evidence_institution ON evidence(institution_id);
CREATE INDEX IF NOT EXISTS idx_institution_name ON institutions(name);
CREATE INDEX IF NOT EXISTS idx_accreditors_name ON accreditors(name);