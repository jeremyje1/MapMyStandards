Service Worker Fix Deployment Notes

Summary:
- A root-scoped service worker previously caused blank app loads. We replaced it with a one-time "killer" SW (`/sw.js`) that unregisters itself and prompts clients to reload.
- We also ensured both `/sw.js` and `/web/sw.js` are served with no-store headers for immediate updates.

Steps to Deploy:
1) Vercel: Trigger a production redeploy of the frontend.
2) Purge cache (if using Vercel Edge caching or a CDN in front) to push the new SW immediately.
3) Ask users to refresh once; the killer SW will unregister any prior SW and reload the page.

Post-Deploy Validation:
- In browser DevTools → Application → Service Workers, confirm no active SW controlling root scope.
- Confirm dashboard and login load normally and network requests are not intercepted by a SW.
