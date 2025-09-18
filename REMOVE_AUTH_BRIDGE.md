# Removing Auth Bridge Workaround

Since the platform already has a custom domain (`platform.mapmystandards.ai`) that shares the same root domain as the API (`api.mapmystandards.ai`), the auth-bridge.js workaround is not necessary.

## Option 1: Keep for Vercel Preview Deployments (Recommended)

Keep the auth-bridge.js in place but make it conditional - only activate when NOT on the production domain:

```javascript
// At the top of auth-bridge.js, add:
(function(){
    // Skip auth bridge on production domain - cookies work natively there
    if (window.location.hostname === 'platform.mapmystandards.ai') {
        return;
    }
    
    // Rest of auth-bridge.js code...
})();
```

This allows the workaround to still function for:
- Vercel preview deployments
- Local development if needed
- Testing on alternative domains

## Option 2: Complete Removal

To completely remove the auth-bridge workaround:

1. Delete `/web/js/auth-bridge.js`
2. Remove `<script src="/js/auth-bridge.js"></script>` from:
   - `/web/login-platform.html`
   - `/web/ai-dashboard.html`
   - `/web/standards.html`
   - `/web/evidence-mapping.html`
   - `/web/reports.html`
   - `/web/org-chart.html`
   - `/web/upload.html`
3. Revert checkAuthentication() functions in standards.html, evidence-mapping.html, and reports.html
4. Revert changes to global-nav.js
5. Remove auth storage calls from login-platform.html

## Recommendation

**Keep Option 1** - Make the auth-bridge conditional. This provides:
- Clean authentication on production (`platform.mapmystandards.ai`)
- Fallback support for development and preview deployments
- No code changes needed in other files
- Easy to disable/enable as needed

## Current Status

The auth-bridge is currently active but not harmful when using the proper domain. Authentication will work correctly via cookies when accessing `platform.mapmystandards.ai`.