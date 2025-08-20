# Railway PostgreSQL Database Setup Guide
**Date**: August 20, 2025  
**Project**: mapmystandards-prod

## ⚠️ Current Status

DATABASE_URL is **NOT** currently set in your Railway environment. This is expected because no PostgreSQL database has been provisioned yet.

## 🗄️ How to Add PostgreSQL to Railway

### Option 1: Using Railway Dashboard (Recommended)

1. **Go to your Railway project**
   - Visit: https://railway.app/dashboard
   - Select `mapmystandards-prod` project

2. **Add PostgreSQL Service**
   - Click "+ New" or "Add Service"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically create the database

3. **Automatic Configuration**
   - Railway will automatically inject `DATABASE_URL` into your app
   - No manual configuration needed
   - The URL includes all connection details

### Option 2: Using Railway CLI

```bash
# From your project directory
railway add

# Select PostgreSQL when prompted
# Railway will provision the database and link it automatically
```

## 🔗 How Railway Handles DATABASE_URL

When you add a PostgreSQL database to your Railway project:

1. **Automatic Injection**: Railway automatically injects the `DATABASE_URL` environment variable
2. **Format**: `postgresql://username:password@host:port/database`
3. **Private Networking**: Uses Railway's internal network for secure, fast connections
4. **No Manual Setup**: You don't need to manually set DATABASE_URL

## 📋 Verify Database Setup

After adding PostgreSQL:

```bash
# Check if DATABASE_URL is present
railway variables | grep DATABASE_URL

# You should see something like:
# DATABASE_URL │ postgresql://postgres:xxxxx@xxxx.railway.app:5432/railway
```

## 🚀 Current Application Configuration

Your application is already configured to use DATABASE_URL:
- **Local Development**: Uses SQLite (`sqlite:///data/a3e_dev.db`)
- **Production**: Will automatically use PostgreSQL when DATABASE_URL is detected

## ✅ Next Steps

1. **Add PostgreSQL** through Railway dashboard or CLI
2. **Deploy your application**: `railway up`
3. **Run migrations** (if needed): 
   ```bash
   railway run python setup_database.py
   ```

## 📝 Important Notes

- Railway PostgreSQL databases are production-ready
- Automatic backups are available (check Railway pricing)
- Connection pooling is handled by Railway
- SSL/TLS is enabled by default
- The database scales with your application

## 🔍 Troubleshooting

If DATABASE_URL is not appearing after adding PostgreSQL:
1. Ensure the database service is linked to your app service
2. Try redeploying: `railway up`
3. Check Railway dashboard for any error messages
4. Verify services are in the same environment

## 💡 Current Database Status

```
❌ PostgreSQL: Not provisioned
❌ DATABASE_URL: Not set
✅ Application: Ready to use DATABASE_URL when provided
✅ Other variables: All configured correctly
```

Once you add PostgreSQL through Railway, DATABASE_URL will be automatically available to your application!
