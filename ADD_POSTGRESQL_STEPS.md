# Adding PostgreSQL to Railway - Step by Step

## 🚀 Quick Steps (Via Dashboard)

1. **Open Railway Dashboard**
   - Go to: https://railway.app/dashboard
   - Select your project: **MapMyStandards**

2. **Add PostgreSQL Service**
   - Click the **"+ New"** button in your project
   - Select **"Database"**
   - Choose **"PostgreSQL"**
   - Click **"Add PostgreSQL"**

3. **PostgreSQL will automatically:**
   - Create a new database instance
   - Generate secure credentials
   - Inject these variables into your environment:
     - `DATABASE_URL` (full connection string)
     - `PGDATABASE` (database name)
     - `PGHOST` (host address)
     - `PGPASSWORD` (password)
     - `PGPORT` (port number)
     - `PGUSER` (username)

## 🔍 Verify PostgreSQL is Added

After adding PostgreSQL, run this command to verify:

```bash
railway variables | grep -E "DATABASE_URL|PG"
```

You should see the PostgreSQL connection details.

## 🗄️ Initialize Database Schema

Once PostgreSQL is added, we need to run migrations:

```bash
# Deploy the application first (includes migration in startup)
railway up

# Monitor the deployment
railway logs --tail
```

## 📝 Update Alembic Configuration for Production

The application will automatically use the DATABASE_URL from environment variables, but let's verify the migration setup: