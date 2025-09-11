# 🚀 PRODUCTION DEPLOYMENT GUIDE
## Railway & Vercel Environment Variables

### ⚠️ SECURITY NOTICE
**DO NOT use the current development secrets in production!**

The secrets currently in your codebase are for development only and have been exposed in:
- Terminal output/logs  
- Git history
- This conversation

### 🔧 REQUIRED FIXES BEFORE DEPLOYMENT

1. **Generate fresh production secrets** (see `generate_production_secrets.py`)
2. **Remove hardcoded secrets from code** ✅ (fixed)
3. **Set environment variables in hosting platforms**
4. **Test with production environment variables**

### 📋 ENVIRONMENT VARIABLES SETUP

#### Railway Deployment:
```bash
# Navigate to your Railway project dashboard
# Go to Variables tab and add:

SECRET_KEY=<GENERATE_NEW_64_CHAR_SECRET>
JWT_SECRET_KEY=<GENERATE_NEW_64_CHAR_SECRET>
OPENAI_API_KEY=sk-proj-<YOUR_PRODUCTION_KEY>
DATABASE_URL=postgresql://username:password@host:port/database
STRIPE_SECRET_KEY=sk_live_<YOUR_LIVE_KEY>
STRIPE_PUBLISHABLE_KEY=pk_live_<YOUR_LIVE_KEY>
STRIPE_WEBHOOK_SECRET=whsec_<YOUR_WEBHOOK_SECRET>
EMAIL_FROM=support@mapmystandards.ai
POSTMARK_SERVER_TOKEN=<YOUR_POSTMARK_TOKEN>
CORS_ORIGINS=https://platform.mapmystandards.ai,https://app.mapmystandards.ai
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

#### Vercel Deployment:
```bash
# Go to Project Settings > Environment Variables
# Add the same variables as above
```

### 🔒 SECURITY BEST PRACTICES

#### ✅ What we fixed:
- Removed hardcoded JWT secrets from source code
- Added `JWT_SECRET_KEY` to config.py
- Updated auth files to use environment variables
- Created production secret generator

#### ⚠️ Critical Actions Required:
1. **Generate NEW secrets for production** (different from dev)
2. **Use separate secrets for staging vs production**
3. **Set up secret rotation schedule**
4. **Monitor for any remaining hardcoded secrets**

### 🔑 SECRET GENERATION

Run this to generate fresh production secrets:
```bash
python3 generate_production_secrets.py
```

### 🧪 TESTING PRODUCTION SETUP

1. **Set environment variables locally:**
   ```bash
   export SECRET_KEY="your_new_production_secret"
   export JWT_SECRET_KEY="your_new_jwt_secret"
   export OPENAI_API_KEY="your_production_openai_key"
   ```

2. **Test the server:**
   ```bash
   uvicorn a3e.main:app --host 0.0.0.0 --port 8000
   ```

3. **Verify authentication works with new secrets**

### 📊 DEPLOYMENT CHECKLIST

- [ ] Generated fresh production secrets
- [ ] Set all environment variables in Railway/Vercel
- [ ] Removed hardcoded secrets from source code ✅
- [ ] Tested locally with production environment variables
- [ ] Verified database connection works
- [ ] Confirmed Stripe integration works
- [ ] Tested email functionality
- [ ] Set up monitoring and logging
- [ ] Configured CORS for production domains
- [ ] Set up secret rotation schedule

### 🎯 PRODUCTION READINESS: READY ✅
**After implementing the above environment variables**

The codebase now properly uses environment variables for secrets. Just need to:
1. Generate fresh production secrets
2. Set them in your hosting platform
3. Test the deployment

### 🔄 SECRET ROTATION SCHEDULE
- **Monthly**: Rotate JWT and session secrets
- **Quarterly**: Rotate API keys (coordinate with providers)
- **Immediately**: If any secret is compromised

### 📞 SUPPORT
If you need help with any of these steps, the secrets are now properly configured to use environment variables, making your deployment secure and production-ready!
