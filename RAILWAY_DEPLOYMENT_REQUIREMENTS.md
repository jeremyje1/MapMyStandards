# Railway Deployment Requirements for New Trial Features

## 🚨 Current Status
**Railway Deployment**: The app is configured but **NOT responding** to health checks
**Domains**: Configured correctly (platform.mapmystandards.ai, api.mapmystandards.ai)
**Issue**: Likely deployment failure due to missing persistent data directories

## ✅ What Railway IS Capturing

### 1. **Application Configuration**
- ✅ **Dockerfile**: Multi-stage build with Node.js + Python
- ✅ **Health Check**: `/health` endpoint configured
- ✅ **Port Handling**: `start.sh` properly uses Railway's PORT variable
- ✅ **Domains**: Custom domains mapped correctly
- ✅ **Git Integration**: Auto-deploys from main branch

### 2. **Environment Variables** (Likely Configured)
- ✅ Basic Python/FastAPI environment
- ✅ CORS origins for platform domains
- ✅ Port configuration (handled by Railway automatically)

## ❌ What Railway is MISSING for New Features

### 1. **Persistent Data Storage** ⚠️ **CRITICAL**
Our new features create local directories that will be **LOST** on Railway restarts:

```bash
# These directories are created at runtime but NOT persistent
jobs_status/           # Job tracking files (.json)
reports_generated/     # Generated PDF reports + status
uploads/               # User uploaded files
```

**Impact**: 
- ✅ Upload works initially
- ❌ Job status lost on restart → broken progress tracking
- ❌ Reports lost on restart → broken download links
- ❌ Files lost on restart → broken analysis continuity

### 2. **Missing Environment Variables**
Our implementation doesn't require additional env vars, but these would be useful:

```bash
# Optional but recommended
FEATURE_DEMO_MODE=true           # Enable sample data
FEATURE_ROI_DEMO=false          # Hide ROI calculations initially  
MAX_FILE_SIZE_MB=100            # File upload limits
ANALYSIS_TIMEOUT_MINUTES=5      # Job timeout settings
```

### 3. **Database Integration** (Future)
Currently using file-based storage, but Railway has:
- ✅ **PostgreSQL**: Available as add-on
- ✅ **Redis**: Available for job queues
- ❌ **Not connected**: Our code uses file system

## 🛠️ Required Railway Fixes

### **IMMEDIATE** (Fix deployment failure):

1. **Add Persistent Volume**:
   ```bash
   # Railway needs to mount persistent storage for:
   /app/jobs_status/
   /app/reports_generated/  
   /app/uploads/
   ```

2. **Environment Variables**:
   ```bash
   railway variables set FEATURE_DEMO_MODE=true
   railway variables set MAX_FILE_SIZE_MB=100
   ```

3. **Redeploy**:
   ```bash
   railway redeploy
   ```

### **SHORT-TERM** (Improve reliability):

1. **Database Migration**:
   - Replace file storage with PostgreSQL
   - Add Redis for job queuing
   - Implement proper data persistence

2. **Health Check Fix**:
   - Ensure `/health` returns 200 consistently
   - Add service dependency checks

### **LONG-TERM** (Production ready):

1. **Proper File Storage**:
   - AWS S3/CloudFlare R2 for uploads
   - Database for job tracking
   - CDN for report downloads

## 📋 Railway Deployment Checklist

### ✅ **Currently Working**:
- [x] Docker build succeeds
- [x] Port configuration correct
- [x] Domain mapping active
- [x] Git auto-deployment
- [x] Basic FastAPI routes

### ❌ **Currently Broken**:
- [ ] Health check responding (app not starting)
- [ ] Persistent data storage
- [ ] File upload persistence  
- [ ] Job tracking across restarts
- [ ] Report generation persistence

### 🔧 **Fix Commands**:

```bash
# 1. Add persistent volume (if Railway supports it)
railway volume create data-storage

# 2. Set required environment variables
railway variables set FEATURE_DEMO_MODE=true
railway variables set PYTHONPATH=/app

# 3. Force redeploy with new commit
git commit --allow-empty -m "Trigger Railway redeploy"
git push origin main

# 4. Check deployment status
railway status
railway logs --tail 50
```

## 🚨 **Critical Issue**: Ephemeral File System

Railway's container restarts **WILL DESTROY**:
- All uploaded files
- All job status tracking  
- All generated reports
- All trial progress data

**This breaks the core trial experience.**

## ✅ **Quick Fix Options**:

### Option 1: **Database Migration** (Recommended)
- Replace file storage with Railway PostgreSQL
- Move job tracking to Redis
- Persistent and scalable

### Option 2: **External Storage**
- AWS S3 for files
- External Redis for jobs
- Works with current code

### Option 3: **Hybrid Approach**
- Keep file system for demo
- Add database for production
- Feature flag controlled

## 🎯 **Next Steps**

1. **URGENT**: Fix Railway health check failure
2. **HIGH**: Implement persistent storage solution  
3. **MEDIUM**: Add proper database integration
4. **LOW**: Optimize for production scale

**The trial features work locally but need persistent storage to work on Railway.**