# User ID Mismatch Fix - Critical Issue

## Problem Identified
The analyze and download features are failing because of a user ID mismatch:

1. **Database Storage**: Documents are stored with UUID user IDs (e.g., `e144cf90-d8ed-4277-bf12-3d86443e2099`)
2. **API Queries**: The API is using email from JWT token (e.g., `jeremy.estrella@gmail.com`)
3. **Result**: SQL queries fail to find documents because user IDs don't match

## Evidence
```sql
-- Document in DB:
user_id: e144cf90-d8ed-4277-bf12-3d86443e2099

-- API query:
WHERE user_id = 'jeremy.estrella@gmail.com'  -- No match!
```

## Solution

### Option 1: Fix the API to Use UUID (Recommended)
Modify the user_intelligence_simple.py to get the correct UUID:

```python
# In each endpoint, replace:
user_id = current_user.get("sub", current_user.get("user_id", "unknown"))

# With:
async def get_user_uuid(current_user: Dict[str, Any]) -> str:
    """Get the actual UUID for the user from the database"""
    email = current_user.get("sub", current_user.get("email"))
    
    async with db_manager.get_session() as session:
        result = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.first()
        if user:
            return user.id
        # Fallback to email if no user found
        return email

# Then use:
user_id = await get_user_uuid(current_user)
```

### Option 2: Add UUID to JWT Token
Modify the token creation to include the UUID:

```python
# When creating JWT token, include:
payload = {
    "sub": user.email,
    "user_id": user.id,  # Add the UUID here
    "email": user.email,
    ...
}
```

### Option 3: Quick Database Fix (Temporary)
Update documents to use email as user_id:

```sql
UPDATE documents 
SET user_id = (SELECT email FROM users WHERE id = documents.user_id)
WHERE user_id IN (SELECT id FROM users);
```

## Immediate Actions

1. **Verify the issue**:
   ```bash
   # Check what user_id format is in documents table
   SELECT DISTINCT user_id, COUNT(*) FROM documents GROUP BY user_id;
   ```

2. **Check JWT token contents**:
   ```python
   # Decode a token to see what's inside
   import jwt
   token = "your_token_here"
   payload = jwt.decode(token, options={"verify_signature": False})
   print(payload)
   ```

3. **Apply the fix** (Option 1 recommended)

## Testing After Fix
1. Clear browser cache and localStorage
2. Login fresh
3. Upload a new document
4. Test analyze and download
5. Verify they work correctly

## Long-term Solution
Standardize on using UUIDs everywhere:
- JWT tokens should include user UUID
- All API endpoints should use UUID
- Database foreign keys should use UUID
- Frontend should never need to know about user IDs