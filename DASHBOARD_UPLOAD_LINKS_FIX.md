# Dashboard Upload Links Fix

## Issue
Dashboard pages were linking to various non-working upload pages:
- `/upload` 
- `/upload-enhanced-v2`
- `/upload-modern`

## Solution
Updated all upload links in dashboard files to point to the working upload page: `/upload-working.html`

## Files Updated

### 1. web/dashboard-enhanced.html (Main Dashboard)
- Updated navigation link: `/upload-enhanced-v2` → `/upload-working.html`
- Updated hero buttons: `/upload` → `/upload-working.html`
- Updated "Upload Documents →" button: `/upload-enhanced-v2` → `/upload-working.html`
- Updated metric card link: `/upload` → `/upload-working.html`
- Updated JavaScript redirect: `/upload-enhanced-v2` → `/upload-working.html`

### 2. web/dashboard-modern.html
- Updated all instances of `/upload-modern` → `/upload-working.html`
- This includes navigation links, action buttons, empty state links, and JavaScript redirects

## Result
Now all upload links from the dashboard will direct users to the working upload page at:
`https://platform.mapmystandards.ai/upload-working.html`

## Notes
- The vercel.json already redirects `/upload` to `/upload-working.html`
- The `/upload-modern` redirects to `/upload` which then goes to `/upload-working.html`
- Direct links to `/upload-working.html` ensure users get to the right page without multiple redirects