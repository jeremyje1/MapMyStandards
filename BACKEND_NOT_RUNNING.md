# Backend Service Not Running - 502 Bad Gateway

## Current Issue
The backend service at `https://api.mapmystandards.ai` is returning 502 Bad Gateway errors, which means:
- The Railway deployment is failing to start
- The application is crashing during startup
- There's a configuration issue preventing the service from running

## This is NOT a CORS Issue
The CORS errors you're seeing are a symptom, not the cause. When the backend is down, no CORS headers are returned, resulting in CORS errors in the browser.

## Immediate Actions Required

### 1. Check Railway Deployment Logs
1. Go to your Railway dashboard
2. Select the backend service
3. Click on "Deployments" tab
4. Check the latest deployment logs for errors

### 2. Common Causes & Solutions

#### Missing Environment Variables
Ensure ALL required environment variables are set in Railway:
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
CORS_ORIGINS=https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://app.mapmystandards.ai
STRIPE_SECRET_KEY=sk_live_... (if using payments)
STRIPE_WEBHOOK_SECRET=whsec_... (if using webhooks)
```

#### Database Connection Issues
- Verify DATABASE_URL is correct
- Check if database is accessible
- Ensure database migrations have run

#### Python Dependencies
The service might be failing due to missing dependencies. Check if all packages in requirements.txt are installing correctly.

### 3. Quick Diagnostic Steps

1. **Check Service Health**
   ```bash
   curl -I https://api.mapmystandards.ai/health
   ```
   Should return 200 OK when running properly.

2. **Check Railway Service Status**
   - Go to Railway dashboard
   - Check if service shows as "Active" or "Failed"
   - Look for crash loops or restart attempts

3. **View Recent Logs**
   Look for error messages like:
   - `ModuleNotFoundError` - Missing Python package
   - `Connection refused` - Database connection issue
   - `KeyError` - Missing environment variable
   - `Invalid configuration` - Config error

### 4. Common Error Patterns

#### Import Errors
```
ModuleNotFoundError: No module named 'xxx'
```
Solution: Check requirements.txt includes all dependencies

#### Database Errors
```
sqlalchemy.exc.OperationalError: connection refused
```
Solution: Verify DATABASE_URL and database accessibility

#### Environment Variable Errors
```
KeyError: 'SECRET_KEY'
```
Solution: Add missing environment variables in Railway

#### Port Binding Errors
```
Error: Invalid port
```
Solution: Ensure using `$PORT` environment variable

### 5. Deployment Configuration Check

Verify your Railway configuration:

**railway.toml:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "sh -c 'python -m uvicorn src.a3e.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 6. Emergency Recovery Steps

If the service won't start:

1. **Rollback to Previous Working Deployment**
   - In Railway, go to Deployments
   - Find last successful deployment
   - Click "Rollback to this deployment"

2. **Check Recent Code Changes**
   Recent commits that might have broken deployment:
   - Webhook implementation
   - Workspace feature
   - CORS configuration updates

3. **Minimal Test Deployment**
   Try deploying a minimal version to isolate issues:
   - Comment out new routers in main.py
   - Disable optional features
   - Test core functionality only

### 7. Once Backend is Running

After fixing the deployment issue:
1. Verify health endpoint: `https://api.mapmystandards.ai/health`
2. Check API docs: `https://api.mapmystandards.ai/docs`
3. Test login functionality
4. Verify CORS headers are present

## Need Help?

If you can't resolve the issue:
1. Share the Railway deployment logs
2. List all environment variables set (without secrets)
3. Share any error messages from the logs