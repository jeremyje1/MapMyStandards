# API Configuration & Health Check Guide

## Centralized API Configuration

This guide documents the centralized API configuration system and health check procedures for MapMyStandards.

## 1. Configuration System

### Core Configuration File

The application uses `web/js/config.js` as the single source of truth for API endpoints:

```javascript
// web/js/config.js
window.MMS_CONFIG = Object.freeze({
    API_BASE_URL: isLocal ? 'http://localhost:8000' : '/api',
    PLATFORM_BASE_URL: isLocal ? 'http://localhost:3000' : 'https://platform.mapmystandards.ai',
    FEATURE_FLAGS: {
        enableRiskOverview: true,
        enableNarrativeExport: true
    }
});
```

### Environment Detection

The configuration automatically detects the environment:
- **Local Development**: Uses `http://localhost:8000` for API calls
- **Production**: Uses relative `/api` paths to leverage Vercel's rewrites

### Implementation Pattern

All HTML files follow this pattern:

```html
<!-- 1. Include config.js -->
<script src="/js/config.js"></script>

<!-- 2. Use buildApiUrl helper -->
<script>
const API_BASE = (window.MMS_CONFIG && window.MMS_CONFIG.API_BASE_URL) || '';

function buildApiUrl(path) {
    if (typeof path !== 'string') return path;
    if (path.startsWith('http')) return path;
    if (!API_BASE) return path;
    if (API_BASE.endsWith('/api') && path.startsWith('/api/')) {
        return API_BASE + path.slice(4);
    }
    return API_BASE + path;
}

// For authenticated requests
async function authFetch(path, options={}) {
    const url = buildApiUrl(path);
    const opts = Object.assign({ credentials:'include' }, options);
    let r = await fetch(url, opts);
    if (r.status === 401 && window.MMS_AUTH?.silentRefresh) {
        await window.MMS_AUTH.silentRefresh();
        r = await fetch(url, opts);
    }
    return r;
}
</script>
```

## 2. Updated Files

All frontend files have been updated to use the centralized configuration:

### Core Application
- ✅ `web/ai-dashboard.html`
- ✅ `web/standards.html`
- ✅ `web/evidence-mapping.html`
- ✅ `web/reports.html`
- ✅ `web/upload.html`

### Authentication & Setup
- ✅ `web/login-platform.html`
- ✅ `web/onboarding.html`
- ✅ `web/trial-signup-new.html`
- ✅ `web/dashboard-original.html`

## 3. Health Check Scripts

### Basic Health Check

**File**: `check_deployment.sh`

Quick verification of core endpoints:

```bash
# Check production
./check_deployment.sh https://api.mapmystandards.ai

# Check local
./check_deployment.sh http://localhost:8000
```

**Checks**:
- `/health` - API health status
- `/` - Root endpoint
- `/docs` - API documentation
- `/health/frontend` - Frontend health

### Extended Health Check

**File**: `check_deployment_extended.sh`

Comprehensive endpoint verification with data validation:

```bash
# Public endpoints only
./check_deployment_extended.sh https://api.mapmystandards.ai

# All endpoints (with authentication)
AUTH_TOKEN="your-bearer-token" ./check_deployment_extended.sh https://api.mapmystandards.ai
```

**Features**:
1. **Basic Health Checks**: Core API endpoints
2. **Public Endpoints**: Standards metadata
3. **Authentication**: Login and Stripe config
4. **Protected Endpoints**: Dashboard, reports, settings
5. **Upload & Processing**: Evidence upload
6. **Cross-References**: Standards matching
7. **Performance**: Response time monitoring

**Output Example**:
```
🔍 Extended Deployment Health Check
=====================================
API Base: https://api.mapmystandards.ai
Time: Wed Sep 17 2025

1. Basic Health Checks
----------------------
✓ API Health: 200 (/health)
✓ Root Endpoint: 200 (/)
✓ API Documentation: 200 (/docs)
✓ Frontend Health: 200 (/health/frontend)

2. Public Endpoints
-------------------
✓ Standards Metadata: 200 with data (/api/user/intelligence-simple/standards/metadata)

3. Authentication Endpoints
---------------------------
✓ Auth Login (Method Check): 405 (/api/auth/login)
✓ Stripe Configuration: 200 (/api/v1/billing/config/stripe-key)

4. Protected Endpoints (with auth)
----------------------------------
✓ Standards List: 200 with data (/api/user/intelligence-simple/standards/list)
✓ Evidence Mapping: 200 with data (/api/user/intelligence-simple/standards/evidence-map)
✓ Dashboard Overview: 200 (/api/user/intelligence-simple/dashboard/overview)
✓ Reports Endpoint: 200 (/api/user/intelligence-simple/reports)
✓ Risk Factors: 200 with data (/api/user/intelligence-simple/risk/factors)
✓ User Settings: 200 (/api/user/intelligence-simple/settings)

5. Upload & Processing
----------------------
✓ Upload Endpoint (Method Check): 405 (/api/user/intelligence-simple/evidence/upload)

6. Standards Cross-References
-----------------------------
✓ Cross-accreditor matching endpoint available

7. API Performance
------------------
✓ Health check response time: 123ms

=====================================
✓ All checks passed!
Deployment is healthy and ready for use.
```

### Deployment Configuration Helper

**File**: `deployment_config.sh`

Environment-specific configuration management:

```bash
# Configure for production
source deployment_config.sh production

# Configure for staging
source deployment_config.sh staging  

# Configure for local development
source deployment_config.sh local

# Run health checks after configuration
check_deployment
```

**Features**:
- Sets environment variables (`TARGET_URL`, `API_BASE_URL`, etc.)
- Provides helper functions (`check_deployment`, `update_frontend_config`)
- Manages environment-specific settings

## 4. Key API Endpoints

### Public Endpoints (No Auth Required)
- `GET /health` - API health status
- `GET /api/user/intelligence-simple/standards/metadata` - Standards corpus metadata
- `GET /api/v1/billing/config/stripe-key` - Stripe public key

### Protected Endpoints (Auth Required)

#### Standards & Compliance
- `GET /api/user/intelligence-simple/standards/list` - List standards
- `GET /api/user/intelligence-simple/standards/evidence-map` - Evidence mapping
- `GET /api/user/intelligence-simple/standards/cross-accreditor-matches` - Cross-references
- `GET /api/user/intelligence-simple/standards/search` - Search standards

#### Dashboard & Reports  
- `GET /api/user/intelligence-simple/dashboard/overview` - Dashboard data
- `GET /api/user/intelligence-simple/reports` - Reports listing
- `POST /api/user/intelligence-simple/narrative/generate` - Generate narratives
- `POST /api/user/intelligence-simple/narrative/export.docx` - Export to Word

#### Evidence & Risk
- `POST /api/user/intelligence-simple/evidence/upload` - Upload documents
- `POST /api/user/intelligence-simple/evidence/analyze` - Analyze evidence
- `GET /api/user/intelligence-simple/risk/factors` - Risk factors
- `POST /api/user/intelligence-simple/risk/score-bulk` - Bulk risk scoring

#### User Management
- `GET /api/user/intelligence-simple/settings` - User settings
- `POST /api/user/intelligence-simple/settings` - Update settings
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

## 5. Deployment Checklist

### Pre-Deployment

- [ ] All API URLs use `buildApiUrl()` or `authFetch()`
- [ ] No hardcoded API endpoints in JavaScript
- [ ] Config.js included in all HTML files
- [ ] Environment variables set in deployment platform
- [ ] CORS configured for production domains

### Post-Deployment

- [ ] Run basic health check: `./check_deployment.sh`
- [ ] Run extended health check: `./check_deployment_extended.sh`
- [ ] Test authenticated endpoints with valid token
- [ ] Verify cross-origin requests work
- [ ] Check browser console for errors

### Monitoring

- [ ] Health endpoint returns 200: `/health`
- [ ] Standards metadata loads: `/api/user/intelligence-simple/standards/metadata`
- [ ] Authentication works: Login and protected endpoints
- [ ] Upload functionality: Evidence can be uploaded
- [ ] Reports generate: Narrative and evidence reports work

## 6. Troubleshooting

### Common Issues

**CORS Errors**
```javascript
// Ensure credentials are included
fetch(url, { credentials: 'include' })

// Check API CORS configuration allows frontend origin
```

**Authentication Failures**
```javascript
// Use authFetch for automatic token refresh
await authFetch('/api/protected-endpoint')

// Manual token handling
headers: { 'Authorization': `Bearer ${token}` }
```

**API Connection Issues**
```bash
# Test API directly
curl -v https://api.mapmystandards.ai/health

# Check with authentication
curl -H "Authorization: Bearer $TOKEN" \
     https://api.mapmystandards.ai/api/user/intelligence-simple/dashboard/overview
```

**Wrong API Base URL**
```javascript
// Verify configuration loaded
console.log('API Base:', window.MMS_CONFIG?.API_BASE_URL);

// Check buildApiUrl output
console.log('Built URL:', buildApiUrl('/api/test'));
```

## 7. Security Best Practices

1. **Use HTTPS** in production
2. **Include credentials** for cookie-based auth
3. **Validate API responses** before using data
4. **Handle errors gracefully** with user feedback
5. **Never expose** sensitive tokens in client code
6. **Use environment variables** for configuration

## Summary

The centralized API configuration ensures consistent API communication across all frontend components. The health check scripts provide comprehensive verification of deployment status, helping identify issues quickly and ensuring smooth deployments.