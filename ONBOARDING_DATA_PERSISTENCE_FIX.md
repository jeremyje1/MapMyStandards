# Onboarding Data Persistence Issue

## Problem
When users complete onboarding (e.g., entering "Houston College" as their institution), the data is only saved to a JSON file via the `/api/user/intelligence-simple/settings` endpoint. It does NOT update the user's `institution_name` field in the PostgreSQL database.

## Current Flow
1. User enters institution name in onboarding
2. Onboarding saves to `/api/user/intelligence-simple/settings`
3. Settings are stored in a JSON file (not the database)
4. User record in database still has blank/original institution_name

## Why This Is a Problem
- User profile doesn't reflect their actual institution
- Customization and analysis can't use the institution data
- Reports and dashboards show generic content instead of Houston College specific

## Solution Needed

### Option 1: Update the Settings Endpoint (Backend Fix)
Modify `/api/user/intelligence-simple/settings` to also update the user record in the database:

```python
@router.post("/settings")
async def save_settings(
    payload: Dict[str, Any], 
    current_user: Dict[str, Any] = Depends(get_current_user_simple),
    db: AsyncSession = Depends(get_db)
):
    # Save to JSON as before
    existing = _merge_claims_with_settings(current_user)
    updated = {**existing, **(payload or {})}
    _save_user_settings(current_user, updated)
    
    # Also update user in database
    if 'organization' in payload:
        user_id = current_user.get('sub') or current_user.get('user_id')
        if user_id:
            stmt = update(User).where(User.id == user_id).values(
                institution_name=payload['organization']
            )
            await db.execute(stmt)
            await db.commit()
    
    return {"status": "saved", "settings": updated}
```

### Option 2: Add a Dedicated User Update Endpoint (Better)
Create a proper user profile update endpoint that updates the database:

```python
@router.put("/user/profile")
async def update_user_profile(
    updates: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_simple),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get('sub') or current_user.get('user_id')
    
    stmt = update(User).where(User.id == user_id).values(
        institution_name=updates.institution_name,
        institution_type=updates.institution_type,
        # other fields...
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "updated"}
```

### Option 3: Frontend Workaround (Temporary)
After onboarding completion, make an additional API call to update the user profile.

## Immediate Workaround
To fix Houston College's data:
1. Manually update the user record in the database
2. Or create a script to sync JSON settings to database

## Testing After Fix
1. Complete onboarding with test institution "Test University 123"
2. Check database: `railway run python3 check_railway_users.py`
3. Verify institution_name is updated in user record