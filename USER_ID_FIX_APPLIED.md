# User ID Fix Applied - Summary

## Changes Made

### 1. Added Helper Function
Added `get_user_uuid_from_email()` function after line 815 in `src/a3e/api/routes/user_intelligence_simple.py`:
```python
async def get_user_uuid_from_email(email: str) -> str:
    """Get the actual UUID for a user from their email address"""
    # Queries the users table to convert email to UUID
    # Falls back to email if no user found (backward compatibility)
```

### 2. Updated Endpoints
Fixed all endpoints that were using email instead of UUID:

1. **GET /uploads/{document_id}** - Download documents ✅
2. **POST /documents/{document_id}/analyze** - Analyze documents ✅
3. **GET /documents/list** - List documents ✅
4. **GET /evidence/list** - List evidence ✅
5. **POST /evidence/upload** - Upload new documents ✅
6. **DELETE /documents/{document_id}** - Delete documents ✅
7. **GET /documents/recent** - Recent documents ✅
8. **GET /compliance/summary** - Compliance dashboard ✅
9. **GET /risk/summary** - Risk dashboard ✅

### 3. Updated Helper Functions
- `_record_user_upload()` - Now converts email to UUID before saving ✅
- `_analyze_evidence_from_bytes()` - Now converts email to UUID for analysis ✅

## Testing Required

1. **Deploy the changes** to Railway
2. **Clear browser cache** and localStorage
3. **Test each feature**:
   - Upload a new document
   - List documents
   - Analyze a document
   - Download a document
   - Delete a document

## Long-Term Fix: Update JWT Token Generation

### Current JWT Token (BAD)
```json
{
  "sub": "jeremy.estrella@gmail.com",
  "user_id": "jeremy.estrella@gmail.com",
  "email": "jeremy.estrella@gmail.com"
}
```

### Desired JWT Token (GOOD)
```json
{
  "sub": "e144cf90-d8ed-4277-bf12-3d86443e2099",
  "user_id": "e144cf90-d8ed-4277-bf12-3d86443e2099",
  "email": "jeremy.estrella@gmail.com"
}
```

### Where to Fix Token Generation

Look for the login/authentication code that creates JWT tokens. It likely looks like:
```python
# CURRENT (needs fixing)
payload = {
    "sub": user.email,
    "user_id": user.email,
    "email": user.email,
    ...
}

# SHOULD BE
payload = {
    "sub": user.id,  # Use UUID
    "user_id": user.id,  # Use UUID
    "email": user.email,  # Keep email for display
    ...
}
```

### Files to Check for JWT Creation
1. `auth.py` or similar authentication module
2. Login endpoints
3. Token refresh endpoints
4. Any place that calls `jwt.encode()`

## Deployment Steps

1. **Commit the changes**:
   ```bash
   git add src/a3e/api/routes/user_intelligence_simple.py
   git commit -m "Fix user ID mismatch: Convert email to UUID in all endpoints"
   git push
   ```

2. **Railway will auto-deploy** (or manually trigger)

3. **Monitor logs** for any errors:
   ```bash
   railway logs --service=prolific-fulfillment --follow
   ```

## Verification

After deployment, run this test:
```python
# Test that endpoints now work
curl -X GET "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/list" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return documents for the correct user
```

## Benefits

1. **Immediate**: All document operations will work correctly
2. **Security**: Users can only access their own documents
3. **Performance**: One extra database query per request (minimal impact)
4. **Compatibility**: Falls back gracefully if email is already a UUID

## Next Steps

1. Apply the long-term fix to JWT token generation
2. Add unit tests for the UUID conversion
3. Consider caching the email-to-UUID mapping for performance
4. Audit all other endpoints for similar issues