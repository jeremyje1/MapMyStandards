# Upload 422 Error Fix

## Issue
The upload was failing with a 422 (Unprocessable Entity) error when trying to upload files to the `/api/user/intelligence-simple/evidence/upload` endpoint.

## Root Cause
The backend FastAPI endpoint expects a form field named `files` (plural) because it's defined to accept a list of files:
```python
files: List[UploadFile] = File(...)
```

However, the frontend was sending the form data with the field name `file` (singular):
```javascript
formData.append('file', file);
```

## Solution
Fixed the form field name in the frontend files to match the backend expectation:

### Files Fixed:
1. **web/upload-working.html** - Changed `formData.append('file', file)` to `formData.append('files', file)`
2. **web/upload-enhanced.html** - Changed `formData.append('file', file)` to `formData.append('files', file)`

### Files Already Correct:
- **web/dashboard-modern.html** - Already using `form.append('files', f)` correctly

## Implementation
The fix was simple - just changing the form field name from singular to plural to match what the backend expects. Even though we're uploading one file at a time, FastAPI expects the field name to be `files` because the endpoint is designed to handle multiple files.

## Testing
After this fix, the upload should work properly. The 422 error should no longer occur, and files should upload successfully to the S3 bucket or local storage as configured.