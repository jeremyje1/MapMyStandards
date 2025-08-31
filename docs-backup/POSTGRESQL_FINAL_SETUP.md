# ✅ Final PostgreSQL Setup Steps

## Current Status
- ✅ PostgreSQL service added (Postgres-RlAi)
- ✅ SQLite DATABASE_URL removed 
- ✅ Application deployed
- ⚠️ Database connection pending

## Required Action in Railway Dashboard

### Step 1: Copy PostgreSQL Credentials
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on **Postgres-RlAi** service
3. Go to **Connect** tab
4. You'll see connection details like:
   ```
   DATABASE_URL: postgres://postgres:PASSWORD@HOST.railway.app:PORT/railway
   ```
5. **Copy the entire DATABASE_URL value**

### Step 2: Add to MapMyStandards Service
1. Click on **MapMyStandards** service
2. Go to **Variables** tab
3. Look for DATABASE_URL
4. If it exists with SQLite value, click edit and replace
5. If it doesn't exist, click **"New Variable"**:
   - Key: `DATABASE_URL`
   - Value: [Paste the PostgreSQL URL from Step 1]
6. Click **"Add"** or **"Update"**

### Step 3: Trigger Redeployment
The service should auto-redeploy. If not:
```bash
railway up
```

## Alternative: Service Linking (Easier!)

In Railway Dashboard:
1. Go to **MapMyStandards** service
2. Click **Settings** tab
3. Find **"Shared Variables"** or **"Service Dependencies"**
4. Select **Postgres-RlAi** from dropdown
5. Click **"Add"**
6. This auto-injects all PostgreSQL variables

## Verification

After deployment completes (2-3 minutes):

### Check API Health:
```bash
curl https://api.mapmystandards.ai/health
```

Should show:
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy"
    }
  }
}
```

### Check Tables Created:
1. Go to **Postgres-RlAi** in Railway
2. Click **"Data"** tab
3. You should see tables:
   - accreditation_standards
   - alembic_version
   - audit_logs
   - compliance_snapshots
   - documents
   - institutions
   - processing_jobs
   - reports
   - standard_mappings
   - users

### Check Application:
- API Docs: https://api.mapmystandards.ai/docs
- Main App: https://platform.mapmystandards.ai

## If Tables Aren't Created

Run migration manually:
```bash
railway run bash
alembic upgrade head
```

## Success Indicators
✅ Health check shows database "healthy"
✅ Tables visible in Postgres-RlAi Data tab
✅ API docs load at /docs
✅ No database errors in logs