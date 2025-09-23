# Database Migration Guide for Persistent Settings

## Current Status
✅ Code deployed with database support
❌ Database tables not yet created
⏳ Migration script needs to be run

## How to Run the Migration

### Option 1: Using Railway CLI (Recommended)
```bash
# From your project directory
railway run python ensure_user_table.py
```

### Option 2: Using Railway Web Console
1. Go to your Railway project dashboard
2. Click on your backend service
3. Go to the "Settings" tab
4. Find "Run Command" section
5. Enter: `python ensure_user_table.py`
6. Click "Run"

### Option 3: One-Click Railway Run Button
Run this command in your terminal:
```bash
railway run --service mapmystandards-api python ensure_user_table.py
```

## What the Migration Does

1. **Connects to PostgreSQL database** using DATABASE_URL
2. **Checks if 'users' table exists**
3. **Creates table if missing** with these fields:
   - id, email, username
   - institution_name, institution_type
   - department, role, primary_accreditor  
   - onboarding_completed (boolean)
   - onboarding_data (JSON)
4. **Verifies all columns exist**

## How to Verify It Worked

### Quick Test:
1. Complete onboarding with test data
2. Log out completely
3. Log back in
4. If you go straight to dashboard = ✅ Success!
5. If asked to onboard again = ❌ Migration needed

### Check Logs:
```bash
railway logs --tail 50 | grep -i "database\|settings saved"
```

Look for:
- "Settings saved to database" = Using database ✅
- "Failed to save settings to database" = Still using JSON ❌

### Direct Database Check:
```bash
railway run --service mapmystandards-api python -c "
import os
from sqlalchemy import create_engine, inspect
engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)
if 'users' in tables:
    cols = [c['name'] for c in inspector.get_columns('users')]
    print('User columns:', cols)
"
```

## Troubleshooting

### If migration fails:
- Check DATABASE_URL is set in Railway
- Ensure PostgreSQL add-on is attached
- Check for connection errors in logs

### If settings still don't persist:
- Migration may have failed silently
- Database connection string might be wrong
- Check Railway logs for errors

## Expected Output
When you run the migration, you should see:
```
🚀 Ensuring User table exists in database

📊 Connecting to database...
🔨 Creating User table...
✅ User table created successfully

✨ Database is ready for user settings!

Onboarding data will now persist across sessions.
```

Or if already exists:
```
✅ User table already exists
   Columns: id, email, username, institution_name, ...
```