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

Upload artifacts to Railway S3 (optional)
- Install SDK once:
  - npm i -D @aws-sdk/client-s3
- Provide AWS creds/target (these are standard Railway variables if you use a Railway S3 plugin or your own bucket):
  - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
  - MMS_ARTIFACTS_BUCKET (or S3_BUCKET): target bucket name
  - MMS_ARTIFACTS_PREFIX (optional, default: `smoke-tests`)
  - MMS_COMMIT_SHA (optional, to group uploads by commit)

Example
```bash
export MMS_BASE=https://platform.mapmystandards.ai
export MMS_API_KEY=YOUR_API_KEY
export AWS_ACCESS_KEY_ID=... 
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
export MMS_ARTIFACTS_BUCKET=railway-your-bucket
export MMS_ARTIFACTS_PREFIX=ui-artifacts
export MMS_COMMIT_SHA=$(git rev-parse --short HEAD)

node scripts/prod_smoke_test.mjs
```
