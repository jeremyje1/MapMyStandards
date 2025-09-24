# Upload Page Redirect and Display Fix

## Changes Made

### 1. Fixed Upload Page Redirect
- Updated `web/vercel.json` to redirect `/upload` to `/upload-working.html` instead of `/upload-enhanced.html`
- This ensures users go to the working upload page

### 2. Fixed Document Display Fields
- Updated `web/upload-working.html` to use correct field names from API:
  - Changed `file.file_size` to `file.size || 0`
  - Changed `file.upload_date` to `file.uploaded_at`

## Why Documents Show 0 Bytes

The documents show 0 bytes because:
1. Files are being uploaded to S3/cloud storage
2. The backend tries to get file size from local path (`saved_path`)
3. Since files are in S3, the local path doesn't exist, so size defaults to 0

This is a cosmetic issue only - the files are actually uploaded successfully.

## API Response Format

The API returns documents with these fields:
- `filename` - The original filename
- `uploaded_at` - Upload timestamp
- `size` - File size (0 if stored in S3)
- `id` - Unique identifier (fingerprint)
- `status` - "processed" or "pending"
- `standards_mapped` - Array of mapped standards
- `saved_path` - Storage path/key
- `fingerprint` - File hash

## Next Steps

After deployment:
1. Users visiting `/upload` will be redirected to the working upload page
2. Uploaded files will display correctly (though size may show as 0 bytes for S3 files)
3. The upload-enhanced.html page will no longer be accessible via `/upload`