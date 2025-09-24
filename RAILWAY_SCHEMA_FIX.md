# 🚨 URGENT: Fix Database Schema on Railway

## Problem
The Railway deployment shows database errors:
- `column "file_key" does not exist`
- `column "user_id" of relation "documents" does not exist`

This indicates the `documents` table exists but with an old schema.

## Quick Fix Options

### Option 1: Run Python Migration Script
1. SSH into Railway service:
   ```bash
   railway run python fix_documents_schema.py
   ```

### Option 2: Direct Database Fix
1. Connect to Railway database:
   ```bash
   railway connect postgres
   ```

2. Run these SQL commands:
   ```sql
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
   ```

### Option 3: Railway CLI (Easiest)
From your terminal in the project directory:

```bash
# Fix the schema
railway run python fix_documents_schema.py

# Or run the shell script
railway run ./railway_fix_schema.sh
```

## After Fixing

1. Check the Railway logs - errors should stop
2. Test upload again at https://platform.mapmystandards.ai/upload-working.html
3. Run console check:
   ```javascript
   const token = localStorage.getItem('access_token');
   fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/uploads', {
     headers: {'Authorization': `Bearer ${token}`}
   }).then(r => r.json()).then(console.log);
   ```

You should now see your uploaded documents!

## Root Cause
The documents table was created with an older schema before we added the file tracking columns. The new code expects these columns but they don't exist in the production database.