# Feature Flag Deployment Playbook

## Staging environment (Railway sandbox)
1. In Railway, open the staging service > **Variables**.
2. Add/update `FEATURE_FLAGS` with JSON enabling all systems, for example:
   ```json
   {
     "standards_graph": true,
     "evidence_mapper": true,
     "evidence_trust_score": true,
     "gap_risk_predictor": true,
     "crosswalkx": true,
     "citeguard": true
   }
   ```
3. Save & redeploy: either push to the staging branch or trigger `railway_deploy.yml` with `workflow_dispatch` targeting the staging service.

## Production (api.mapmystandards.ai)
1. Decide which features are ready to expose.
2. Set `FEATURE_FLAGS` in the production Railway environment with only the approved keys set to `true`.
3. Trigger the GitHub Action `Railway Deploy` workflow on branch `main` to roll out.
4. Verify `GET https://api.mapmystandards.ai/api/v1/feature-flags` returns expected payload.

## Vercel frontend preview
1. In the Vercel dashboard, go to **Project → Settings → Environment Variables**.
2. Add the same `FEATURE_FLAGS` JSON for the Preview environment if the static site needs to know the default state (optional).
3. Run the `Deploy to Vercel` workflow or push to `main`; Vercel picks up environment vars automatically.

## Rolling out algorithms
- Replace stub payloads in `src/a3e/api/routes/intelligence_showcase.py` with real service calls, one module at a time.
- Keep stub structures as fallback: wrap real logic in a `try/except` and return placeholder data on failure.
- Update the corresponding Cypress intercepts under `web/cypress/e2e/intelligence-stubs.cy.js` to assert new fields.
- Expand backend smoke tests in `tests/test_intelligence_showcase.py` to cover success + error paths.

## Deployment order
1. Merge backend changes into `main`, run `Railway Deploy` (staging), verify.
2. Merge frontend updates; run `Deploy to Vercel` (Preview) if needed.
3. Promote to production by rerunning both workflows with environment `production`.

Document last updated: 2025-10-10.
