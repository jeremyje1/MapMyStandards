# Cross-Domain Authentication Bridge Implementation

## Problem
The session wasn't persisting outside of the AI Dashboard. When users clicked to other pages like Standards Explorer, the header would show "Guest (Session: inactive)" despite being logged in on the AI Dashboard.

## Root Cause
The authentication cookies were being set for the `.mapmystandards.ai` domain, but the frontend was deployed on Vercel using a `vercel.app` domain. Cookies cannot be shared between these different domains due to browser security policies.

## Solution Implemented
Created a client-side authentication bridge using sessionStorage as a fallback mechanism for cross-domain authentication.

## Files Modified

### 1. Created `/web/js/auth-bridge.js`
- New authentication bridge module that stores authentication data in sessionStorage
- Provides methods: `storeAuth()`, `getStoredAuth()`, `clearAuth()`, and `checkAuth()`
- Automatically expires sessions after 24 hours
- Falls back to sessionStorage when cookies aren't available

### 2. Updated `/web/login-platform.html`
- Added auth-bridge.js script
- Modified successful login handler to call `MMS_AUTH_BRIDGE.storeAuth()` 
- Ensures authentication data is stored in sessionStorage upon login
- Also handles demo login path

### 3. Updated Authentication Pages
Modified checkAuthentication() functions in:
- `/web/standards.html`
- `/web/evidence-mapping.html`  
- `/web/reports.html`

Each now:
- Checks auth-bridge first for stored session
- Falls back to regular API auth check if no stored session
- Stores successful API auth responses for future use

### 4. Updated `/web/js/global-nav.js`
- Added auth-bridge check before making API calls
- Stores successful auth responses from API
- Clears sessionStorage on logout
- Ensures auth persistence across all pages

### 5. Added auth-bridge.js to All Pages
Ensured script is loaded before global-nav.js on:
- `/web/ai-dashboard.html`
- `/web/standards.html`
- `/web/evidence-mapping.html`
- `/web/reports.html`
- `/web/org-chart.html`
- `/web/upload.html`

## How It Works

1. **Login Flow:**
   - User logs in on login-platform.html
   - On successful login, auth data is stored in both cookies AND sessionStorage
   - User is redirected to AI Dashboard or requested page

2. **Page Navigation:**
   - When loading any page, auth-bridge checks sessionStorage first
   - If found and valid (< 24 hours old), uses stored auth
   - If not found, falls back to cookie-based API auth check
   - Any successful API auth is stored for future use

3. **Logout Flow:**
   - User clicks logout
   - Both cookies and sessionStorage are cleared
   - User is redirected to login page

## Testing Instructions

1. Clear all browser data (cookies and localStorage/sessionStorage)
2. Go to the login page and sign in
3. Navigate between different pages (AI Dashboard, Standards, Evidence Mapping, Reports)
4. Verify that the user remains authenticated on all pages
5. Test logout functionality to ensure session is properly cleared

## Future Considerations

Once the frontend is deployed to a subdomain of mapmystandards.ai (e.g., app.mapmystandards.ai), the cookie domain mismatch will be resolved and this bridge can be removed. The auth-bridge serves as a temporary workaround for the Vercel deployment.