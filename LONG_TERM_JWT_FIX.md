# Long-Term JWT Fix - Implementation Guide

## Current Issue
JWT tokens are created with email as the user identifier, causing mismatches with database UUIDs.

## Files That Need Updating

### 1. Primary Token Creation: `src/a3e/api/routes/auth_impl.py`

**Current Code (Line 74-86):**
```python
def create_jwt_token(email: str, remember: bool = False) -> str:
    """Create JWT token for authenticated user"""
    expiration = timedelta(hours=JWT_EXPIRATION_HOURS * (30 if remember else 1))
    expire = datetime.utcnow() + expiration
    
    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

**Fix Required:**
```python
def create_jwt_token(user: User, remember: bool = False) -> str:
    """Create JWT token for authenticated user"""
    expiration = timedelta(hours=JWT_EXPIRATION_HOURS * (30 if remember else 1))
    expire = datetime.utcnow() + expiration
    
    payload = {
        "sub": str(user.id),  # Use UUID
        "user_id": str(user.id),  # Explicit user_id field
        "email": user.email,  # Keep email for display
        "name": user.name,  # Include name for UI
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

### 2. Update Callers: `src/a3e/api/routes/auth_db.py`

**Lines to fix:**
- Line 126: `access_token = create_jwt_token(user.email)`
- Line 201: `access_token = create_jwt_token(user.email)`

**Change to:**
```python
access_token = create_jwt_token(user)  # Pass user object instead of email
```

### 3. Good Example Already Exists: `src/a3e/api/routes/auth_enhanced.py`

This file already does it correctly!

**Line 141 (register):**
```python
access_token = create_access_token({"sub": str(user.id), "email": user.email})
```

**Line 230 (login):**
```python
access_token = create_access_token({"sub": str(user.id), "email": user.email})
```

## Migration Strategy

Since `auth_enhanced.py` already creates proper tokens, consider:

1. **Switch to using auth_enhanced.py** for all authentication
2. **OR update auth_impl.py** to match the pattern

## Testing After Fix

1. **Create a test user and login**:
```python
# Decode the token to verify structure
import jwt
token = "your_new_token_here"
payload = jwt.decode(token, options={"verify_signature": False})
print(payload)

# Should show:
{
  "sub": "e144cf90-d8ed-4277-bf12-3d86443e2099",  # UUID
  "user_id": "e144cf90-d8ed-4277-bf12-3d86443e2099",  # UUID
  "email": "jeremy.estrella@gmail.com",
  "exp": 1234567890,
  "iat": 1234567890
}
```

2. **Remove the helper function** we added (optional):
Once JWT tokens contain UUIDs, the `get_user_uuid_from_email()` function becomes unnecessary.

## Benefits of This Fix

1. **Performance**: No extra database query per request
2. **Consistency**: UUID used everywhere
3. **Security**: Better separation of identity (UUID) vs contact info (email)
4. **Scalability**: UUIDs are better for distributed systems

## Deployment Order

1. **Deploy the current fix first** (helper function) - DONE ✅
2. **Update JWT token creation** (this fix)
3. **Test thoroughly**
4. **Optional: Remove helper function** after all users have new tokens

## Backward Compatibility

The helper function we added handles both cases:
- Old tokens (email in 'sub') → converts to UUID
- New tokens (UUID in 'sub') → uses UUID directly

This allows gradual migration without breaking existing sessions.