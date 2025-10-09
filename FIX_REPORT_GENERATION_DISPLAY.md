# Fix for Static Report Generation Display

## Problem
Every document upload produces the same report with hardcoded data:
- 87% Overall Coverage
- 73 Standards Mapped
- 5 Evidence Documents
- 12 Gap Areas

This is because `/report-generation` serves a static HTML file with hardcoded values.

## Root Cause
The file `web/report-generation.html` contains hardcoded values that are shown to users after document analysis, regardless of the actual analysis results.

## Solution Options

### Option 1: Update Frontend to Show Real Analysis Results (Recommended)
Instead of redirecting to the static page, show the analysis results in the React app:

1. After document upload completes, fetch the actual analysis results
2. Display them in a React component with real data
3. Remove any links/redirects to `/report-generation`

### Option 2: Make report-generation.html Dynamic
Convert the static HTML to fetch real data via API:

```javascript
// Add to report-generation.html
async function loadRealMetrics() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/user/intelligence-simple/dashboard/metrics', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        // Update display with real data
        document.querySelector('.summary-value').textContent = Math.round(data.compliance_score) + '%';
        document.querySelector('.standards-mapped').textContent = data.standards_mapped;
        document.querySelector('.documents-count').textContent = data.documents_analyzed;
        // etc...
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

// Call on page load
window.addEventListener('DOMContentLoaded', loadRealMetrics);
```

### Option 3: Remove Static Page Access
Disable the `/report-generation` route in the backend and ensure all report generation goes through the React app.

## Immediate Fix

To implement Option 2 quickly, update `web/report-generation.html`:

1. Replace hardcoded values with placeholders
2. Add JavaScript to fetch real data from API
3. Update values dynamically when page loads

## Long-term Solution

The best approach is to handle all reporting within the React application:
1. Create a proper report generation component
2. Fetch real analysis data from the API
3. Display dynamic, real-time results
4. Remove reliance on static HTML files

## Implementation Steps

1. **Quick Fix** (for immediate deployment):
   - Update `web/report-generation.html` to fetch real data
   - Deploy to production

2. **Proper Fix** (for next sprint):
   - Create React component for report display
   - Integrate with existing API endpoints
   - Remove static HTML dependencies

This will ensure users see their actual document analysis results instead of placeholder data.