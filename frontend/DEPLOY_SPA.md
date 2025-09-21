# Deploying the SPA to platform.mapmystandards.ai

Ensure env is set for production:
  - `.env.production` contains:
    - `REACT_APP_API_URL=https://api.mapmystandards.ai`
    - `REACT_APP_APP_URL=https://platform.mapmystandards.ai`
Choose a host (Vercel or Netlify). Both configs are present:
  - Vercel: `frontend/vercel.json`
  - Netlify: `frontend/netlify.toml`
Build and deploy:

```bash
cd frontend
npm ci
npm run build
# Vercel
npx vercel --prod
# or Netlify
netlify deploy --prod --dir=build
```

DNS: point `platform.mapmystandards.ai` to your host.
Redirects: legacy routes redirect to SPA:
  - `/login-platform(.html)?` → `/login`
  - `/dashboard-modern` → `/dashboard`
  - `/reports-modern` → `/reports`
  - `/standards-modern` → `/standards`
SPA fallback is configured so deep links load `index.html`.

## Post-deploy checks
Visit `https://platform.mapmystandards.ai/login` and sign in.
Confirm Dashboard, Standards, Reports, Crosswalk routes function.
Validate CORS with API at `https://api.mapmystandards.ai`.