# Analyze & Download Fix - Root Cause Confirmed

## Executive Summary
The analyze and download features are failing because:
- **JWT tokens contain email addresses** (e.g., `jeremy.estrella@gmail.com`)
- **Database stores UUIDs** (e.g., `e144cf90-d8ed-4277-bf12-3d86443e2099`)
- **API queries fail** because they compare email to UUID

## Confirmed Evidence

### JWT Token Contents
```json
{
  "sub": "jeremy.estrella@gmail.com",
  "user_id": "jeremy.estrella@gmail.com",  // Should be UUID!
  "email": "jeremy.estrella@gmail.com"
}
```

### Database Reality
```sql
-- Documents table:
user_id: e144cf90-d8ed-4277-bf12-3d86443e2099 (UUID)

-- API query:
WHERE user_id = 'jeremy.estrella@gmail.com'  -- MISMATCH!
```

## Why Delete Works But Analyze/Download Don't

Looking at the code:
- **Delete** might be using a different auth mechanism or was fixed earlier
- **Analyze/Download** are using the raw JWT claims without UUID lookup

## The Fix

### Immediate Solution (Backend Only)

1. **Add this helper function** to `src/a3e/api/routes/user_intelligence_simple.py`:

```python
# Add after line 815 (after get_current_user_simple function)
async def get_user_uuid_from_email(email: str) -> str:
    """Get the actual UUID for a user from their email address"""
    try:
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
    except Exception as e:
        logger.error(f"Error getting user UUID: {e}")
        return email
```

2. **Update these specific endpoints**:

For `/uploads/{document_id}` (line ~2633):
```python
# Replace:
user_id = current_user.get("sub", current_user.get("user_id", "unknown"))

# With:
email = current_user.get("sub", current_user.get("email", "unknown"))
user_id = await get_user_uuid_from_email(email)
```

For `/documents/{document_id}/analyze` (line ~2685):
```python
# Same replacement as above
```

For `/documents/list` (line ~2850):
```python
# Same replacement as above
```

For `/evidence/list` (line ~2271):
```python
# Same replacement as above
```

### Testing Steps
1. Apply the code changes
2. Restart the backend
3. Clear browser cache
4. Login fresh
5. Your existing documents should now be accessible
6. Analyze and download should work

## Long-term Fix (Recommended)

Fix the JWT token generation to include the UUID:
```python
# In the login/token generation code:
payload = {
    "sub": user.id,  # Use UUID instead of email
    "user_id": user.id,  # UUID
    "email": user.email,  # Keep email for display
    "full_name": user.full_name
}
```

## Why This Happened

This is a common issue when:
1. Initial development uses email as the primary identifier
2. Later, the database switches to UUIDs for better practice
3. But the authentication layer isn't updated to match

## Action Items

1. **Immediate**: Apply the backend fix to unblock users
2. **This week**: Update JWT token generation to use UUIDs
3. **Future**: Audit all endpoints for consistent user ID handling