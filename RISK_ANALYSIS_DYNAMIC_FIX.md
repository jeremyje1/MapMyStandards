# Dynamic Risk Analysis Fix

## Problem Statement
The risk analysis feature provided AI-assisted risk scores with factors like evidence coverage, trust, and staleness, and listed predicted issues. However, **the risk scores remained static because evidence was never mapped**, making the GapRisk Predictor™ essentially non-functional with static demo data.

## Solution Implemented

### 1. Dynamic Risk Calculation API
**File: `src/a3e/api/routes/risk_analysis_dynamic.py`**
- Created new API endpoints that calculate risk scores from actual database evidence:
  - `POST /api/v1/risk/score-standard-dynamic` - Calculate risk for a single standard
  - `GET /api/v1/risk/standard/{code}/risk-summary` - Get comprehensive risk summary
  - `POST /api/v1/risk/bulk-score-dynamic` - Bulk score multiple standards

### 2. Real Evidence Data Integration
**Function: `get_evidence_data_for_standard()`**
- Queries actual StandardMapping table for evidence
- Calculates real metrics:
  - Coverage percentage based on document count and quality
  - Trust scores from mapping confidence values
  - Evidence age from document upload dates
  - Verification status counts

### 3. Dynamic Coverage Calculation
```python
if evidence_count == 0:
    coverage = 0.0
elif evidence_count == 1:
    coverage = min(trust_scores[0] * 60, 60)  # Max 60% for single evidence
elif evidence_count >= 3 and verified_count >= 1:
    coverage = min(avg_trust * 100, 95)  # Max 95% for multiple verified
else:
    coverage = min(avg_trust * 80, 80)  # Max 80% for multiple unverified
```

### 4. Enhanced Risk Predictions
- Added specific issues based on real evidence gaps:
  - "No evidence mapped - complete documentation gap"
  - "Single evidence source - requires additional supporting documents"
  - "No verified evidence - requires reviewer validation"
  - "Evidence averaging X days old - refresh recommended"
  - "Low confidence scores - evidence may not adequately support standard"

### 5. Frontend Integration
**File: `web/standards-modern.html`**
- Updated risk modal to use dynamic API endpoint
- Added evidence metadata display in risk modal
- Clear risk cache when evidence is mapped/unmapped
- Shows real-time evidence counts and verification status

### 6. Real-Time Updates
- Added `cacheClearRiskScore()` function
- Risk scores refresh automatically after evidence mapping
- Cache cleared for affected standards when evidence changes

## Technical Details

### API Response Structure
```json
{
  "success": true,
  "data": {
    "standard_id": "8.1",
    "risk_score": 0.42,
    "risk_level": "medium",
    "predicted_issues": [
      "Single evidence source - requires additional supporting documents",
      "No verified evidence - requires reviewer validation"
    ],
    "evidence_metadata": {
      "evidence_count": 1,
      "verified_count": 0,
      "average_confidence": 75.0,
      "data_source": "database"
    }
  }
}
```

### Risk Factors Now Dynamic
1. **Coverage**: Calculated from actual mapped documents
2. **Trust**: Average of evidence confidence scores
3. **Staleness**: Days since document upload
4. **Task Debt**: From compliance status tracking
5. **Historical Findings**: From compliance history

## Usage Flow

1. **View Initial Risk**
   - Standards show risk scores based on current evidence
   - Click "Risk Factors" to see detailed breakdown

2. **Map Evidence**
   - Select standards and map documents
   - Risk cache automatically cleared

3. **View Updated Risk**
   - Risk scores recalculated with new evidence
   - Predicted issues reflect actual gaps

4. **Evidence Impact Visible**
   - Modal shows evidence count and verification
   - Trust scores affect risk calculations
   - Age of evidence factors into staleness

## Result
- ✅ Risk scores now change dynamically based on mapped evidence
- ✅ Predicted issues reflect actual evidence gaps
- ✅ Coverage percentage calculated from real document mappings
- ✅ Trust scores derived from mapping confidence values
- ✅ Evidence age tracked and affects risk calculations
- ✅ Real-time updates when evidence is added/removed

The GapRisk Predictor™ now functions as advertised, providing meaningful risk assessments that change based on actual evidence mapping activities.