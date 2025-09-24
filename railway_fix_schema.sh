#!/bin/bash
# Fix documents table schema on Railway

echo "🔧 Fixing documents table schema on Railway..."

# Get Railway database credentials
DB_HOST=$(railway variables get PGHOST)
DB_PORT=$(railway variables get PGPORT)
DB_NAME=$(railway variables get PGDATABASE)
DB_USER=$(railway variables get PGUSER)
DB_PASSWORD=$(railway variables get PGPASSWORD)

# Connect to Railway database and fix schema
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF

-- Check current schema
\d documents

-- Add missing columns
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_key VARCHAR(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sha256 VARCHAR(64);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'uploaded';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Verify final schema
\d documents

-- Check for any existing data
SELECT COUNT(*) as document_count FROM documents;

EOF

echo "✅ Schema fix complete!"