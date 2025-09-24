# 🚨 IMMEDIATE ACTION: Fix Database Schema

## Current Status
✅ Backend deployed to Railway at 10:28 AM  
❌ Database schema error preventing uploads from being saved

## Error Details
From Railway logs:
```
column "file_key" does not exist
column "user_id" of relation "documents" does not exist
```

## SOLUTION: Run This SQL on Railway Database

### Method 1: Railway Dashboard (Easiest)
1. Go to Railway dashboard: https://railway.app/
2. Click on your PostgreSQL database (Postgres-RlAi)
3. Click "Connect" → "Query"
4. Copy and paste this SQL:

```sql
-- Fix documents table schema
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

5. Click "Run Query"

### Method 2: Using psql (if Method 1 doesn't work)
1. Get connection string from Railway:
   - Go to your Postgres-RlAi service
   - Click "Connect"
   - Copy the `DATABASE_URL`

2. Run:
   ```bash
   psql "YOUR_DATABASE_URL" < fix_schema.sql
   ```

## Verification
After running the fix:

1. Check Railway logs - errors should stop appearing
2. Test upload at: https://platform.mapmystandards.ai/upload-working.html
3. Verify in browser console:
   ```javascript
   const token = localStorage.getItem('access_token');
   fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/uploads', {
     headers: {'Authorization': `Bearer ${token}`}
   }).then(r => r.json()).then(console.log);
   ```

You should see your uploaded documents instead of empty array!

## Why This Happened
- The `documents` table exists but with an old schema
- The backend code expects new columns that don't exist yet
- This one-time fix adds the missing columns

## Success Indicators
- No more database errors in Railway logs
- Uploads persist after page refresh
- Console command shows uploaded files