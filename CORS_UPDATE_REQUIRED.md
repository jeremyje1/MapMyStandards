# CORS Origins Update Required

## Current Issue
The CORS_ORIGINS environment variable in Railway is currently set to:
```
https://platform.mapmystandards.ai,https://app.mapmystandards.ai
```

This is causing CORS errors when the frontend tries to communicate with the backend API.

## Important Note
The backend code (src/a3e/main.py) should automatically add `https://api.mapmystandards.ai` to the allowed origins, but this might not be working due to:
1. The deployed code being outdated
2. An error during startup
3. The CORS middleware not being properly initialized

## Solution
Update the CORS_ORIGINS variable in Railway to include all necessary domains:

```
https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://app.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai
```

## How to Update in Railway

1. Go to your Railway dashboard
2. Select your backend service  
3. Click on "Variables" tab
4. Find the `CORS_ORIGINS` variable
5. Update the value to:
   ```
   https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://app.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai
   ```
6. Click "Save"
7. The service will automatically redeploy

## Why This Is Needed
Even though `https://api.mapmystandards.ai` is where your backend is hosted, it still needs to be in the CORS allowed origins list because:
1. The browser checks the Origin header against the allowed list
2. Cross-origin requests (from platform.mapmystandards.ai to api.mapmystandards.ai) require explicit permission
3. The backend needs to send the proper Access-Control-Allow-Origin headers

## Verification
After updating and redeploying:
1. Clear your browser cache
2. Try logging in at https://platform.mapmystandards.ai/login
3. Check the browser console - CORS errors should be resolved
4. Check Network tab - API requests should succeed with proper CORS headers

## Alternative Solutions

### 1. Force Redeploy
If updating CORS_ORIGINS doesn't work, try forcing a redeploy:
- In Railway dashboard, go to your backend service
- Click "Redeploy" to ensure the latest code is running

### 2. Check Deployment Logs
Look for these messages in Railway logs:
- `CORS configured allow_origins=...` - Should show all allowed origins
- Any error messages during startup

### 3. Test CORS Headers
Run the included script to test CORS headers:
```bash
./check_cors_headers.sh
```

This will show if the API is returning proper CORS headers.

### 4. Temporary Workaround
If urgent, you can set a wildcard CORS (NOT for production):
```
CORS_ORIGINS=*
```

### 5. Check if Backend is Running
Verify the API is accessible:
- https://api.mapmystandards.ai/health
- https://api.mapmystandards.ai/docs