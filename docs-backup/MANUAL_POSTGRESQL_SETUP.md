# Manual PostgreSQL Setup for Railway

## Current Status
✅ PostgreSQL database added (Postgres-RlAi)
✅ Application deployed to Railway
⏳ Tables need to be created

## Option 1: Connect PostgreSQL in Railway Dashboard

1. **Go to your PostgreSQL service** (Postgres-RlAi) in Railway
2. **Click on "Variables" tab**
3. **Copy the DATABASE_URL** value
4. **Go to your MapMyStandards service**
5. **Click on "Variables" tab**
6. **Add/Update DATABASE_URL** with the PostgreSQL connection string
7. **Redeploy the service**

## Option 2: Use Railway CLI to Link Services

In Railway Dashboard:
1. Click on your **MapMyStandards** service
2. Go to **Settings** tab
3. Under **Service Dependencies**, add **Postgres-RlAi**
4. This will automatically inject PostgreSQL variables

## Option 3: Manual Database URL Format

If you need to set it manually, the PostgreSQL URL format is:
```
postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway
```

Set it using:
```bash
railway variables --set "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
```

## After Connecting PostgreSQL

Once the DATABASE_URL is properly set:

1. **Redeploy the application:**
   ```bash
   railway up
   ```

2. **The startup script will automatically:**
   - Connect to PostgreSQL
   - Run Alembic migrations
   - Create all tables
   - Start the server

3. **Verify tables were created:**
   - Go to Postgres-RlAi in Railway Dashboard
   - Check the "Data" tab
   - You should see tables like:
     - institutions
     - users
     - documents
     - reports
     - accreditation_standards
     - etc.

## Troubleshooting

If tables aren't created:

1. **Check logs for errors:**
   ```bash
   railway logs
   ```

2. **Common issues:**
   - DATABASE_URL not set correctly
   - PostgreSQL service not linked
   - Migration files not included in deployment
   - Connection timeout

3. **Manual migration (if needed):**
   ```bash
   # Connect to Railway shell
   railway run alembic upgrade head
   ```

## Verification

Your deployment is successful when:
- PostgreSQL shows tables in the Data tab
- Application logs show "Database schema initialized"
- You can access https://api.mapmystandards.ai/docs
- Health check at https://api.mapmystandards.ai/health returns OK