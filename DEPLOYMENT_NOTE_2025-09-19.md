# MapMyStandards — Prod Deployment Note (2025-09-19)

This deploy aligns production with the ICX demo flow. It includes:
- GET alias for BYOL reload: `/api/user/intelligence-simple/standards/byol/reload`
- Status aliases: `/api/user/intelligence-simple/standards/corpus/status`, `/api/user/intelligence-simple/standards/status`, `/api/user/intelligence-simple/standards/corpusstatus`
- Minimal debug route: `/debug/router-presence`
- Frontend fallbacks + auth on admin/crosswalk pages

## 1) Railway: Set environment variable

Set redacted mode in backend:

```zsh
railway variables --set "STANDARDS_DISPLAY_MODE=redacted"
```

Confirm:
```zsh
railway variables | grep STANDARDS_DISPLAY_MODE
```

## 2) Deploy backend (Railway)

Trigger a redeploy so new routes are live:

```zsh
# From repo root
railway up
# or, if using GitHub integration, push main and let Railway build
# git push origin main
```

Monitor:
```zsh
railway logs --tail
```

Health check:
```zsh
./check_deployment.sh
```

## 3) Post-deploy verification (curl)

Router presence (should return JSON with flags and sample paths):
```zsh
curl -sS https://api.mapmystandards.ai/debug/router-presence | jq .
```

Status endpoints (expect 200 with JSON after auth):
```zsh
# Obtain a JWT via your normal login flow, then:
TOKEN="<paste JWT>"
for p in \
  /api/user/intelligence-simple/standards/corpus/status \
  /api/user/intelligence-simple/standards/status \
  /api/user/intelligence-simple/standards/corpusstatus \
  /api/user/intelligence-simple/standards/metadata \
  /api/user/intelligence-simple/standards/corpus/metadata \
; do echo "\n== $p =="; curl -sS -H "Authorization: Bearer $TOKEN" https://api.mapmystandards.ai$p | jq '. | {ok: .success, keys: (keys)}'; done
```

BYOL reload (idempotent; use GET if POST blocked):
```zsh
# POST
curl -sS -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"path":"byol/standards","fallback_to_seed":true}' \
     https://api.mapmystandards.ai/api/user/intelligence-simple/standards/byol/reload | jq .
# GET alias
curl -sS -H "Authorization: Bearer $TOKEN" \
     "https://api.mapmystandards.ai/api/user/intelligence-simple/standards/byol/reload?path=byol/standards&fallback_to_seed=true" | jq .
```

Standards list should return items and display_mode:
```zsh
curl -sS -H "Authorization: Bearer $TOKEN" \
  'https://api.mapmystandards.ai/api/user/intelligence-simple/standards/list?limit=1' | jq .
```

## 4) UI checks

- Admin: https://api.mapmystandards.ai/admin-standards?token=<JWT>
  - Upload BYOL corpus (YAML/JSON), Reload Graph, Refresh Status
  - Expect display badge to show `display: redacted` once env var is set
- CrosswalkX: https://api.mapmystandards.ai/crosswalkx?token=<JWT>
  - Compute across two accreditors; requires loaded corpus
- Reviewer Portal: https://api.mapmystandards.ai/reviewer-portal
  - Load hosted reviewer pack and follow PDF anchors

## 5) Rollback

If needed, redeploy previous image in Railway or revert commit on main and redeploy.

## 6) Notes

- Some environments block POST on certain paths; use provided GET aliases where applicable.
- Status and metadata endpoints are protected; ensure Authorization header is present.
- The frontend pages were updated to include token-in-URL capture and proper auth headers.
