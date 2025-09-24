-- Fix documents table schema to match what the backend expects
-- Run this in Railway PostgreSQL database

-- Add missing columns if they don't exist
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'uploaded';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Add any other missing columns that might be needed
ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_path TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);

-- Create evidence_mappings table if it doesn't exist
CREATE TABLE IF NOT EXISTS evidence_mappings (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    standard_id VARCHAR(255) NOT NULL,
    confidence FLOAT DEFAULT 0,
    excerpts JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, standard_id)
);

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_evidence_mappings_document_id ON evidence_mappings(document_id);
CREATE INDEX IF NOT EXISTS idx_evidence_mappings_standard_id ON evidence_mappings(standard_id);

-- Display table structure to verify
\d documents
\d evidence_mappings