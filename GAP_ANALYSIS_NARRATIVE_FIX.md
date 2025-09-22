# Gap Analysis & Narrative Generation Fix

## Issue Summary
The dashboard had links to "Analyze Gaps" and "Narrative (CiteGuard)" features that:
1. Redirected to the reports page which showed "no mapped evidence found yet"
2. Displayed empty narrative templates
3. Were not operational without properly mapped evidence

## Root Causes
1. Gap analysis and narrative buttons redirected to `/reports#gaps` and `/reports#narrative` but these sections didn't exist on the reports page
2. No dedicated pages for gap analysis or narrative generation
3. Narrative generation API exists but wasn't connected to a user interface

## Solution Implemented

### 1. Created Gap Analysis Page
**File:** `web/gap-analysis.html`
- Dedicated page for compliance gap analysis
- Shows metrics: Overall compliance %, Accreditation readiness %, Critical gaps count
- Lists critical gaps (standards with no evidence or low confidence)
- Provides prioritized action items
- Export functionality for gap analysis reports
- Empty state handling when no evidence is mapped

### 2. Created Narrative Generator Page  
**File:** `web/narrative.html`
- Full-featured narrative generation interface branded as "CiteGuard"
- Standard selection dropdown populated from mapped evidence
- Four narrative types:
  - Comprehensive (detailed with full citations)
  - Concise (focused with key highlights)
  - Gap-Focused (emphasizes areas needing improvement)
  - Strength-Focused (highlights institutional strengths)
- Real-time narrative generation with citations
- Edit capabilities with toolbar
- Export options: Word, PDF (placeholder), HTML
- Word count tracking
- Empty state handling

### 3. Updated Dashboard Navigation
**File Modified:** `web/dashboard-modern.html`
- Changed gap analysis link from `#gap-analysis` to `/gap-analysis`
- Changed narrative link from `#narrative` to `/narrative`  
- Updated button click handlers to navigate to new pages

### 4. Added Routes to Backend
**File Modified:** `src/a3e/main.py`
- Added `/gap-analysis` route serving `gap-analysis.html`
- Added `/narrative` route serving `narrative.html`
- Both routes include fallback to reports page if files not found

## Technical Implementation

### Gap Analysis Logic
```javascript
// Analyzes evidence data to categorize gaps:
- Critical: Standards with no evidence
- High: Standards with <50% confidence
- Medium: Standards with 50-80% confidence
- Generates actionable recommendations
```

### Narrative Generation
```javascript
// Connects to existing API endpoint:
POST /api/v1/narratives/evidence
// Falls back to client-side mock generation
// Processes citations with tooltips
// Supports editing and export
```

## Result
1. **Gap Analysis** now provides:
   - Real-time analysis of compliance gaps
   - Visual metrics showing readiness status
   - Prioritized action items
   - Export capabilities

2. **Narrative Generator (CiteGuard)** now provides:
   - AI-powered narrative generation with evidence citations
   - Multiple narrative styles for different needs
   - Full editing capabilities
   - Professional export options

## User Experience Improvements
- Clear navigation from dashboard to dedicated tools
- No more empty templates or confusing redirects
- Actionable insights from gap analysis
- Professional narratives ready for accreditation submissions

## Next Steps
1. Enhance narrative generation with more sophisticated AI prompts
2. Add PDF export functionality (currently placeholder)
3. Implement action plan tracking from gap analysis
4. Add collaborative editing features for narratives