# MapMyStandards Deployment Quick Start Guide

## 🚀 Overview

This guide helps you quickly deploy and verify the MapMyStandards platform with the new centralized API configuration and health checks.

## 📋 Pre-Deployment Checklist

1. **Environment Variables Set**:
   ```bash
   # Check required environment variables
   echo "DATABASE_URL: ${DATABASE_URL:-(not set)}"
   echo "STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY:-(not set)}"
   echo "JWT_SECRET: ${JWT_SECRET:-(not set)}"
   ```

2. **Configuration Files Updated**:
   - `web/js/config.js` - API endpoints configured
   - Backend environment variables loaded
   - Database migrations applied

## 🏃‍♂️ Quick Deployment Steps

### 1. Local Development

```bash
# Set environment to local
source deployment_config.sh
set_environment local

# Start backend
python a3e_main_deploy.py

# Start frontend (in another terminal)
cd web
python -m http.server 8080

# Run health check
./check_deployment_extended.sh
```

### 2. Staging Deployment

```bash
# Set environment to staging
source deployment_config.sh
set_environment staging

# Deploy to staging
railway up -e staging

# Wait for deployment to complete, then:
./check_deployment_extended.sh
```

### 3. Production Deployment

```bash
# Set environment to production
source deployment_config.sh
set_environment production

# Deploy to production
railway up -e production

# Run production health check
./check_deployment_extended.sh

# Monitor deployment
check_deployment_health
```

## 🧪 Testing Configuration

### Browser Test
1. Open `https://yourdomain.com/test-api-config.html`
2. Click "Run API Tests" to verify endpoints
3. Click "Test Auth Endpoints" (login required)

### Command Line Test
```bash
# Quick health check
curl -s https://yourdomain.com/health | jq .

# Check standards loaded
curl -s https://yourdomain.com/api/user/intelligence-simple/standards/metadata | jq '.accreditors | length'

# Should return 6 (all accreditors loaded)
```

### Authenticated Test
```bash
# Get auth token (replace with your credentials)
TOKEN=$(curl -s -X POST https://yourdomain.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | jq -r .access_token)

# Test protected endpoint
curl -s https://yourdomain.com/api/user/intelligence-simple/dashboard/overview \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## 📊 Health Check Results

A successful deployment shows:

```
=== MapMyStandards Deployment Health Check ===
✅ Public API Endpoints
   ✓ Health Check: 200 OK (120ms)
   ✓ Stripe Config: 200 OK (45ms)
   
✅ Standards API
   ✓ Metadata: 200 OK - 6 accreditors loaded
   ✓ Standards List: 200 OK - 135 total standards
   
✅ Evidence Mapping
   ✓ Cross-Accreditor: 200 OK - Matching functional
   
✅ Reports API
   ✓ Gap Analysis: 200 OK
```

## 🔧 Common Issues & Solutions

### API 404 Errors
```bash
# Check if config.js is loaded
curl -s https://yourdomain.com/js/config.js

# Verify API_BASE_URL is set correctly
grep API_BASE_URL web/js/config.js
```

### Standards Not Loading
```bash
# Check YAML files
python -c "import yaml; yaml.safe_load(open('data/standards/sacscoc.yaml'))"

# Verify standards endpoint
curl -s https://yourdomain.com/api/user/intelligence-simple/standards
```

### Authentication Failures
```bash
# Check JWT secret is set
echo $JWT_SECRET

# Test login endpoint
curl -X POST https://yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## 📱 Mobile & Cross-Origin

If accessing from mobile or different domain:

1. Update CORS settings in backend
2. Ensure cookies are set with proper domain
3. Test with:
   ```bash
   curl -I https://yourdomain.com/api/health \
     -H "Origin: https://mobile.yourdomain.com"
   ```

## 🎯 Next Steps

1. **Monitor Performance**: 
   ```bash
   # Run performance test
   ./check_deployment_extended.sh --performance
   ```

2. **Enable Features**:
   - Update `FEATURE_FLAGS` in config.js
   - Deploy and verify with health check

3. **Scale Up**:
   - Monitor response times in health check output
   - Scale instances if >500ms average response time

## 📞 Support

- Check logs: `railway logs`
- Run diagnostics: `./check_deployment_extended.sh --verbose`
- Review configuration: `cat web/js/config.js`

---

**Quick Reference Commands:**
```bash
# Full deployment cycle
source deployment_config.sh && \
set_environment production && \
railway up -e production && \
sleep 30 && \
./check_deployment_extended.sh
```