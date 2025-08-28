# PostgreSQL Setup for Railway

## Manual Steps Required in Railway Dashboard:

1. **Add PostgreSQL to your Railway project:**
   - Go to https://railway.app/project/1a6b310c-fa1b-43ee-96bc-e093cf175829
   - Click "New Service" → "Database" → "Add PostgreSQL"
   - Wait for PostgreSQL to provision

2. **Connect PostgreSQL to your app:**
   - In your app service settings
   - Go to Variables tab
   - Add reference variable: `DATABASE_URL` → `${{Postgres.DATABASE_URL}}`
   - Remove the current `DATABASE_URL=sqlite:///./a3e.db`

3. **Update these environment variables:**
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=30
   ALLOW_START_WITHOUT_DB=false
   ```

## Automatic Database Initialization

The application will automatically:
- Create tables on first startup
- Run migrations if needed
- Initialize with seed data

## Verification

After deployment, check:
```bash
curl https://api.mapmystandards.ai/health
```

Look for: `"database": {"status": "healthy"}`