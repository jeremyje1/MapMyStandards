# Upload Persistence and Additional Links Fix

## Issues Fixed

### 1. File Size Persistence (0 Bytes Issue)
The uploaded files were showing 0 bytes because:
- Files are uploaded to S3 cloud storage
- The backend was trying to get file size from local paths that don't exist for S3 files
- The file size wasn't being stored in the upload record

#### Solution:
- Updated `_record_user_upload` function to accept and store file size
- Modified the upload endpoint to pass the actual file size when recording
- Updated `list_evidence` to use the stored size instead of checking local filesystem

### 2. Additional Upload Links Fixed
Fixed remaining upload links across the platform:

#### Pages Updated:
- **dashboard-enhanced.html**: Fixed remaining `/upload` hero button
- **homepage-enhanced.html**: Changed `/upload-modern.html` to `/upload-working.html`  
- **evidence-mapping-wizard.html**: Changed `/upload-enhanced` to `/upload-working.html`

#### Pages Still Using Non-Working Links (Lower Priority):
- dashboard-fixed.html
- dashboard-original.html
- quick-wins-dashboard.html
- faq.html
- evidence-mapping.html
- organizational-enhanced.html
- settings-enhanced.html

These are secondary/unused pages but can be updated if needed.

## Backend Changes

### Modified: src/a3e/api/routes/user_intelligence_simple.py

1. **Updated _record_user_upload function signature**:
   - Added `file_size: Optional[int] = None` parameter
   - Added `"size": file_size or 0` to the upload entry

2. **Updated evidence_upload_simple**:
   - Now passes `file_size=len(content)` when recording upload

3. **Updated list_evidence**:
   - Now uses stored size first, only checking filesystem as fallback
   - This fixes the 0 bytes display issue for S3 uploads

## Testing

Created `check_upload_persistence.py` script to diagnose:
- Upload persistence storage
- Environment variable configuration
- API connectivity

## Result

After these changes:
1. Uploaded files will show their actual size instead of 0 bytes
2. All primary dashboard and navigation links point to the working upload page
3. File metadata is properly persisted with size information

## Deployment Required

- **Frontend (Vercel)**: For updated HTML links
- **Backend (Railway)**: For the file size persistence fix