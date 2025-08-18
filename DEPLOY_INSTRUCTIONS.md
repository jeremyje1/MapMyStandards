# Manual Deployment Instructions

## Current Status
- ✅ Canvas dependency removed from package.json
- ✅ Vercel.json updated for Next.js auto-detection  
- ✅ GitHub Actions workflow created for automated deployment
- ✅ Deploy scripts created
- ⏳ Waiting for Command Line Tools installation to complete

## Next Steps (Manual)

### 1. Wait for CLT Installation
Wait for the Command Line Tools installation dialog to complete. This was triggered by `xcode-select --install`.

### 2. Run Deployment Script
Once CLT installation finishes:
```bash
./deploy_complete.sh
```

### 3. Alternative: Manual Git Commands
If the script fails, run these commands manually:
```bash
git add -A
git commit -m "chore: canvas fix, vercel config, deploy automation"
git push -u origin main
```

### 4. Vercel Deployment Options

#### Option A: GitHub Actions (Automatic)
- Push triggers the workflow in `.github/workflows/vercel_deploy.yml`
- Requires these secrets in GitHub repo settings:
  - VERCEL_TOKEN
  - VERCEL_ORG_ID  
  - VERCEL_PROJECT_ID

#### Option B: Vercel Dashboard (Manual)
1. Go to vercel.com
2. Find your MapMyStandards project
3. Go to Deployments tab
4. Click "Redeploy" on the latest deployment
5. Enable "Clear build cache" if needed

#### Option C: Vercel CLI (After Node.js installed)
```bash
# Install Node.js first
brew install node
# Then deploy
npx vercel deploy --prod --force
```

## What's Fixed
- Canvas build errors (removed native dependency)
- Vercel config simplified (auto Next.js detection)
- Added automation for future deployments

## Files Changed
- `package.json` - Removed canvas dependency
- `vercel.json` - Removed custom builds config
- `scripts/generate_og_images.mjs` - Made canvas optional
- `.github/workflows/vercel_deploy.yml` - Added CI/CD
- `deploy_complete.sh` - One-click deployment script

Run `./deploy_complete.sh` when ready!
