# CORS Configuration Fix Guide

## Problem
The frontend at `https://platform.mapmystandards.ai` is unable to communicate with the backend API at `https://api.mapmystandards.ai` due to CORS (Cross-Origin Resource Sharing) policy blocking the requests.

## Error Message
```
Access to fetch at 'https://api.mapmystandards.ai/api/auth/login' from origin 'https://platform.mapmystandards.ai' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The backend API server is not configured with the proper CORS_ORIGINS environment variable in the Railway deployment.

## Solution

### 1. Set CORS_ORIGINS Environment Variable in Railway

You need to add the following environment variable to your Railway backend deployment:

```
CORS_ORIGINS=https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai,https://app.mapmystandards.ai,http://localhost:3000,http://localhost:3001,http://localhost:8000
```

### 2. How to Add in Railway

#### Option A: Using Railway CLI
```bash
railway variables set CORS_ORIGINS="https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai,https://app.mapmystandards.ai,http://localhost:3000,http://localhost:3001,http://localhost:8000"
```

#### Option B: Using Railway Dashboard
1. Go to your Railway project dashboard
2. Select your backend service
3. Click on "Variables" tab
4. Click "Add Variable"
5. Add:
   - Key: `CORS_ORIGINS`
   - Value: `https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai,https://app.mapmystandards.ai,http://localhost:3000,http://localhost:3001,http://localhost:8000`
6. Click "Save"

### 3. Verify Other Required Environment Variables

Make sure these are also set in Railway:
- `DATABASE_URL` - Your PostgreSQL connection string
- `SECRET_KEY` - Your secret key for sessions
- `JWT_SECRET_KEY` - Your JWT secret for authentication
- `STRIPE_SECRET_KEY` - Your Stripe secret key (if using payments)
- `STRIPE_WEBHOOK_SECRET` - Your Stripe webhook secret (if using webhooks)

### 4. Restart the Service

After adding the environment variable, Railway should automatically redeploy your service. If not, manually redeploy from the Railway dashboard.

## Code Reference

The CORS configuration is handled in `/src/a3e/main.py` (lines 523-559):

```python
# Add CORS middleware (parse comma-separated env var properly)
_cors_origins: list[str] = []
try:
    if isinstance(settings.cors_origins, str):
        _cors_origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
    else:  # type: ignore
        _cors_origins = list(settings.cors_origins)  # type: ignore
except Exception:
    _cors_origins = []

# Ensure platform + api domains are allowed (idempotent append)
for required_origin in [
    "https://platform.mapmystandards.ai",
    "https://api.mapmystandards.ai",
    "https://mapmystandards.ai",
    "https://www.mapmystandards.ai",
    "https://app.mapmystandards.ai",  # React app on Railway
    "http://localhost:8000",
    "http://localhost:3000",  # React dev server
    "http://localhost:3001",  # Alternative React port
    "http://localhost:8888",  # Local static server / alt dev port
]:
    if required_origin not in _cors_origins:
        _cors_origins.append(required_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)
```

## Testing

After deploying with the correct CORS_ORIGINS:

1. Open browser developer console
2. Go to `https://platform.mapmystandards.ai/login`
3. Try logging in
4. Check that no CORS errors appear in the console
5. Verify successful API calls in Network tab

## Alternative: Wildcard CORS (NOT Recommended for Production)

If you need a quick fix for testing only, you can set:
```
CORS_ORIGINS=*
```

**WARNING**: This allows requests from any origin and should NEVER be used in production!

## Additional Notes

- The backend automatically adds common MapMyStandards domains to CORS even if not in the environment variable
- CORS preflight requests are cached for 24 hours (86400 seconds) to improve performance
- All HTTP methods and headers are allowed for authenticated requests