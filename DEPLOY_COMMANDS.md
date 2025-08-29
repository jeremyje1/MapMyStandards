# Railway Deployment Commands

## After Adding PostgreSQL, Run These Commands:

### 1. Verify PostgreSQL is Connected
```bash
railway variables | grep DATABASE_URL
```

### 2. Deploy the Application
```bash
railway up
```

### 3. Monitor Deployment Logs
```bash
railway logs --tail
```

### 4. Check Deployment Status
```bash
railway status
```

### 5. Open Your Application
```bash
railway open
```
Or visit directly:
- Main App: https://platform.mapmystandards.ai
- API Docs: https://api.mapmystandards.ai/docs

## 🔍 What Happens During Deployment:

1. **Docker Build**: Railway builds your Docker image
2. **Database Connection**: Waits for PostgreSQL to be ready
3. **Migrations Run**: Alembic creates all database tables
4. **Schema Init**: Ensures all tables exist
5. **Server Starts**: FastAPI starts on port 8000
6. **Health Check**: Railway verifies the app is responding

## 🚨 Troubleshooting:

If deployment fails, check:
```bash
# View detailed logs
railway logs

# Check if PostgreSQL is properly connected
railway variables | grep DATABASE

# Restart the deployment
railway restart
```

## ✅ Success Indicators:

Your deployment is successful when:
- Logs show: "✅ Database connection successful!"
- Logs show: "✅ Database schema initialized"
- Logs show: "🌐 Starting FastAPI server on port 8000"
- Health check passes (green status in Railway)
- You can access https://platform.mapmystandards.ai