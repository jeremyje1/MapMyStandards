# Duplicate Upload Fix - Complete

## Issue
When uploading a document, the system was creating two entries:
1. An initial document with 0 bytes marked as "analyzed" 
2. The actual document with file content

## Root Cause
The upload flow was calling `_record_user_upload` twice:
1. First in the main upload endpoint (`evidence_upload_simple`) at line 2143
2. Second in the `_analyze_evidence_from_bytes` function at line 660

This created two separate document records in the database.

## Solution Implemented

### 1. Modified `_analyze_evidence_from_bytes` function
- Added optional `document_id` parameter
- When document_id is provided, updates the existing document instead of creating a new one
- Updates both the documents table and evidence_mappings table with analysis results

### 2. Updated all callers
- Main upload endpoint now passes `document_id` to the analysis function
- Analyze endpoint also passes `document_id` to prevent duplicate creation

### 3. Key Changes
```python
# Added document_id parameter
async def _analyze_evidence_from_bytes(
    filename: str,
    content: bytes,
    doc_type: Optional[str],
    current_user: Dict[str, Any],
    document_id: Optional[str] = None,  # NEW PARAMETER
):

# Update existing document instead of creating new one
if document_id:
    # UPDATE documents SET... WHERE id = document_id
    # INSERT INTO evidence_mappings...
else:
    # Original behavior: create new record
```

## Testing Steps
1. Upload a new document
2. Verify only ONE document appears in the list
3. Check that document has correct file size (not 0 bytes)
4. Confirm analyze button works without creating duplicates
5. Verify download functionality works

## Deployment
- Changes committed and pushed to main branch
- Railway will auto-deploy the backend
- No frontend changes required

## Additional Notes
- The fix maintains backward compatibility
- Existing duplicate documents can be cleaned up manually if needed
- The analyze endpoint now properly updates existing documents