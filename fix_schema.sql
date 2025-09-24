-- Fix documents table schema
-- Add missing columns for upload functionality

ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'uploaded';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Show final schema
\d documents