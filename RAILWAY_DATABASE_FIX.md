# Railway Database URL Fix

## The Issue
The backend is failing with 500 errors because the DATABASE_URL is set to the private Railway URL which only works within Railway's network:
- Current (private): `postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@postgres-rlai.railway.internal:5432/railway`
- Should be (public): `postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway`

## Quick Fix
1. Go to your Railway project
2. Go to the backend service
3. Go to Variables tab
4. Update DATABASE_URL to:
   ```
   postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway
   ```

## Why This Happens
- Railway provides two database URLs:
  - **Private URL** (`*.railway.internal`): Only works within Railway's network
  - **Public URL** (`*.proxy.rlwy.net`): Works from anywhere
- The backend is trying to connect using the environment variable
- If the private URL is set, it can't connect and returns 500 errors

## Alternative Solutions

### Option 1: Use Railway's Database URL Reference
Instead of hardcoding, use Railway's reference:
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Option 2: Check in Railway
1. Go to your PostgreSQL service in Railway
2. Look for the "Connect" tab
3. Copy the "Public Connection String"
4. Use that as DATABASE_URL in your backend service

## Testing
After updating, test with:
```bash
curl https://api.mapmystandards.ai/api/auth/test
curl https://api.mapmystandards.ai/api/auth/test-db
```

The first should work regardless, the second will confirm database connectivity.