# MapMyStandards Platform Access Guide

## ✅ CORRECT URL TO USE
**Always access the platform via: https://platform.mapmystandards.ai**

## ❌ DO NOT USE
- Do not use the Vercel deployment URL (e.g., `*.vercel.app`)
- This will cause authentication issues due to cookie domain mismatch

## Why This Matters

The MapMyStandards platform uses secure HTTP-only cookies for authentication. These cookies are configured for the `.mapmystandards.ai` domain to ensure they work across all subdomains:

- Frontend: `platform.mapmystandards.ai`
- Backend API: `api.mapmystandards.ai`
- Marketing site: `mapmystandards.ai`

When you access the platform via the Vercel URL, the browser cannot access cookies set for `.mapmystandards.ai`, causing the authentication to fail on page navigation.

## Quick Links

### Platform Access
- **Login**: https://platform.mapmystandards.ai/login-platform
- **AI Dashboard**: https://platform.mapmystandards.ai/ai-dashboard
- **Standards Explorer**: https://platform.mapmystandards.ai/standards
- **Evidence Mapping**: https://platform.mapmystandards.ai/evidence-mapping
- **Reports**: https://platform.mapmystandards.ai/reports
- **Trial Signup**: https://platform.mapmystandards.ai/trial-signup-stripe.html

### API Endpoints
- **Base API URL**: https://api.mapmystandards.ai
- **Auth Check**: https://api.mapmystandards.ai/auth/me
- **Standards API**: https://api.mapmystandards.ai/standards

## Troubleshooting

If you experience authentication issues:

1. **Clear all cookies** for both domains:
   - Clear cookies for `*.vercel.app`
   - Clear cookies for `*.mapmystandards.ai`

2. **Use an incognito/private window** to test fresh authentication

3. **Always start from**: https://platform.mapmystandards.ai/login-platform

4. **Verify the URL bar** shows `platform.mapmystandards.ai` (not `vercel.app`)

## For Developers

### Environment Configuration
The platform automatically detects the environment and configures the API URL:
- Production: Uses `https://api.mapmystandards.ai`
- Local development: Uses `http://localhost:8000`

### Cookie Configuration
- Domain: `.mapmystandards.ai` (works for all subdomains)
- Secure: `true` (HTTPS only)
- HttpOnly: `true` (prevents XSS attacks)
- SameSite: `None` (allows cross-site requests with CORS)

## Summary

The authentication bridge workaround implemented earlier is **NOT needed** when accessing the platform via the proper domain. Simply use `https://platform.mapmystandards.ai` and authentication will work seamlessly across all pages.