-- Fix association tables with correct data types

-- Drop existing tables if they have wrong types
DROP TABLE IF EXISTS institution_accreditor CASCADE;
DROP TABLE IF EXISTS evidence_standard CASCADE;
DROP TABLE IF EXISTS evidence CASCADE;

-- Create evidence table with correct institution_id type
CREATE TABLE IF NOT EXISTS evidence (
    id VARCHAR(36) PRIMARY KEY,
    institution_id VARCHAR(36) REFERENCES institutions(id),
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

-- Create the association tables with correct types
CREATE TABLE IF NOT EXISTS institution_accreditor (
    institution_id VARCHAR(36) REFERENCES institutions(id),
    accreditor_id VARCHAR REFERENCES accreditors(id),
    PRIMARY KEY (institution_id, accreditor_id)
);

CREATE TABLE IF NOT EXISTS evidence_standard (
    evidence_id VARCHAR(36) REFERENCES evidence(id),
    standard_id VARCHAR REFERENCES standards(id),
    confidence_score FLOAT DEFAULT 0.0,
    mapped_by_agent BOOLEAN DEFAULT TRUE,
    verified_by_human BOOLEAN DEFAULT FALSE,
    mapping_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (evidence_id, standard_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_evidence_institution ON evidence(institution_id);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);
CREATE INDEX IF NOT EXISTS idx_institution_accreditor_inst ON institution_accreditor(institution_id);
CREATE INDEX IF NOT EXISTS idx_institution_accreditor_acc ON institution_accreditor(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_evidence_standard_evidence ON evidence_standard(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_standard_standard ON evidence_standard(standard_id);