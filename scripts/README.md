Prod UI Smoke Test
===================

Prereqs
- Node 18+
- Playwright: `npm i -D playwright && npx playwright install chromium`

Run
```bash
# Set your prod creds (either works)
export MMS_BASE=https://platform.mapmystandards.ai
export MMS_API_KEY=YOUR_API_KEY_HERE
# or
# export MMS_JWT=YOUR_JWT_HERE

node scripts/prod_smoke_test.mjs
```

Outputs
- Screenshots and CSV saved under `./artifacts/`:
  - `evidence-mapping.png`
  - `reports-gap.png`
  - `gap-analysis.csv`
