# Database Backend Update Summary

## Changes Made

### 1. Updated user_intelligence_simple.py to use PostgreSQL instead of JSON

#### Imports Added:
- `from ...models.document import Document as DocumentModel`
- `import uuid`

#### Functions Converted to Async Database Operations:

1. **`_get_user_uploads()`** - Now queries the `documents` table:
   - Fetches up to 50 most recent documents for the user
   - Returns documents with all metadata including size
   - No longer reads from JSON file

2. **`_record_user_upload()`** - Now inserts into `documents` table:
   - Creates a new document record with all metadata
   - Stores file size, SHA256 hash, and file key
   - Returns updated upload list from database

3. **Removed `_set_user_uploads()`** - No longer needed with database

#### Functions Updated to Use Async Calls:
- `evidence_upload_simple()` - Uses `await _record_user_upload()`
- `list_evidence()` - Uses `await _get_user_uploads()`
- `_compute_dashboard_metrics_for_snapshot()` - Made async and uses `await _get_user_uploads()`
- Multiple other endpoints updated to await async calls

### 2. Created ensure_documents_table.py
- Script to verify documents table exists
- Can be run to ensure database schema is ready

## Benefits

1. **Persistence**: Uploads now survive Railway deployments
2. **Reliability**: No more JSON file corruption issues
3. **Scalability**: Handles concurrent uploads properly
4. **Performance**: Database queries are more efficient than loading entire JSON file

## Deployment Steps

1. **Deploy Backend to Railway**
   - The code will automatically use the existing `documents` table
   - If table doesn't exist, it will be created on first database connection

2. **Run Migration (Optional)**
   - If you have existing uploads in JSON, run: `python apply_upload_migration.py`
   - This will migrate JSON data to the database

3. **Verify**
   - Upload a file and check it persists after Railway restart
   - Files should show proper sizes instead of 0 bytes

## Next Steps

Consider adding:
- Indexes on `user_id` and `uploaded_at` for better query performance
- Mapping table to store standard associations
- Soft delete functionality (using `deleted_at` field)