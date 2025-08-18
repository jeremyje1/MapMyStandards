# Vercel Project Configuration

**Project ID:** prj_535SlKWMzZrP8HHG0Mb44JAIEK97
**Project Name:** map-my-standards  
**Team/Org:** jeremys-projects-73929cad
**Current URL:** map-my-standards-5dkpsyoi6-jeremys-projects-73929cad.vercel.app

## GitHub Secrets Required

Add these in GitHub repository Settings → Secrets and variables → Actions:

1. **VERCEL_TOKEN** - Your Vercel API token
2. **VERCEL_ORG_ID** - Your team/org ID: `jeremys-projects-73929cad`

The VERCEL_PROJECT_ID is hardcoded in the workflow as: `prj_535SlKWMzZrP8HHG0Mb44JAIEK97`

## Manual Deploy Commands

If you want to deploy via CLI:
```bash
npx vercel --prod --token YOUR_TOKEN --scope jeremys-projects-73929cad
```

Or link the project first:
```bash
npx vercel link --project prj_535SlKWMzZrP8HHG0Mb44JAIEK97
npx vercel deploy --prod
```
