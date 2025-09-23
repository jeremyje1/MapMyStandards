# Deploy Enhanced Pages - Quick Guide

## Current Status
✅ Pages Created (in `/web` directory):
- standards-graph-enhanced.html
- compliance-dashboard-enhanced.html  
- reports-enhanced.html
- organizational-enhanced.html
- settings-enhanced.html
- about-enhanced.html
- contact-enhanced.html

❌ Pages Not Accessible (404 errors on platform.mapmystandards.ai)

## Deploy to Production (2 minutes)

```bash
# Navigate to web directory
cd web

# Deploy to Vercel production
vercel --prod

# Or if you need to login first
vercel login
vercel --prod
```

## Update Vercel Configuration

Add these rewrites to `web/vercel.json`:

```json
{
  "rewrites": [
    // ... existing rewrites ...
    { "source": "/standards-graph", "destination": "/standards-graph-enhanced.html" },
    { "source": "/compliance-dashboard", "destination": "/compliance-dashboard-enhanced.html" },
    { "source": "/reports", "destination": "/reports-enhanced.html" },
    { "source": "/organizational", "destination": "/organizational-enhanced.html" },
    { "source": "/settings", "destination": "/settings-enhanced.html" },
    { "source": "/about", "destination": "/about-enhanced.html" },
    { "source": "/contact", "destination": "/contact-enhanced.html" }
  ]
}
```

## Fix Authentication Error

The login API is returning 500 error. Check Railway logs:

```bash
# View recent logs
railway logs

# Or check specific service
railway logs -s backend
```

Likely issues:
1. Database connection error
2. Missing environment variables
3. CORS configuration

## Post-Deployment Testing

After deployment, test all links:

1. Visit https://platform.mapmystandards.ai/login-enhanced.html
2. Try logging in with test credentials
3. Navigate through all menu items
4. Verify no 404 errors

## Quick Fixes Needed

### 1. Update Navigation Links
All enhanced pages need to update their navigation to use relative paths:

```html
<!-- Current (broken) -->
<a href="standards-graph-enhanced.html">Standards Graph</a>

<!-- Should be (to work with Vercel rewrites) -->
<a href="/standards-graph">Standards Graph</a>
```

### 2. Fix Mobile Menu
Add hamburger menu for mobile devices in all pages.

### 3. Add Loading States
Add loading indicators while API calls are in progress.

## Verification Checklist

After deployment:
- [ ] All pages load without 404
- [ ] Login works without 500 error  
- [ ] Navigation between pages works
- [ ] Mobile view is responsive
- [ ] API calls show loading states
- [ ] Error messages are user-friendly

## Emergency Rollback

If something breaks after deployment:

```bash
# List recent deployments
vercel ls

# Rollback to previous version
vercel rollback [deployment-url]
```