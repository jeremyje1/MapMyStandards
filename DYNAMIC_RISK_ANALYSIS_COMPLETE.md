# Dynamic Risk Analysis Implementation - Complete

## Overview
The GapRisk Predictor™ now dynamically updates risk scores in real-time as evidence is mapped to or removed from standards.

## Key Features Implemented

### 1. Event-Driven Architecture
- Custom `evidenceMapped` events are dispatched whenever evidence is mapped or unmapped
- Event listeners automatically trigger risk score recalculation
- Works across all evidence mapping workflows

### 2. Real-Time Updates
- Risk scores update immediately when:
  - Evidence is mapped via the pipeline workflow
  - Evidence is mapped from the evidence library
  - Evidence mappings are removed
  - Documents are uploaded and mapped

### 3. Visual Feedback
- Risk buttons show updated risk levels with color-coded indicators:
  - 🟢 Green dot = Low Risk
  - 🟡 Yellow dot = Medium Risk  
  - 🔴 Red dot = High Risk
- Temporary checkmark appears when risk is recalculated
- Risk modal updates if open during changes

### 4. Smart Caching
- LRU cache system prevents unnecessary API calls
- Cache is cleared for affected standards when evidence changes
- Automatic cache eviction when capacity reached

## Technical Implementation

### Event Dispatch Points
1. **Pipeline Mapping** (lines 3934-3939)
   ```javascript
   selectedStandards.forEach(standardId => {
       window.dispatchEvent(new CustomEvent('evidenceMapped', {
           detail: { standardId }
       }));
   });
   ```

2. **Evidence Library Mapping** (lines 4544-4549)
   ```javascript
   window.dispatchEvent(new CustomEvent('evidenceMapped', {
       detail: { standardId }
   }));
   ```

3. **Mapping Removal** (lines 6788-6791)
   ```javascript
   window.dispatchEvent(new CustomEvent('evidenceMapped', {
       detail: { standardId }
   }));
   ```

### Update Function (lines 6851-6908)
```javascript
async function updateRiskDisplay(standardId) {
    // Find risk button with flexible selector
    // Fetch fresh risk score from API
    // Update button visual with risk level
    // Add temporary success indicator
    // Update cache with new score
    // Refresh modal if open
}
```

### Event Listener (lines 6837-6847)
```javascript
window.addEventListener('evidenceMapped', (event) => {
    // Update evidence library if open
    // Clear cache for affected standard
    // Trigger risk display update
});
```

## User Experience

### Before
- Risk scores remained static after evidence mapping
- Users had to refresh page to see updated risks
- No visual feedback on risk changes

### After  
- Risk scores update instantly when evidence is mapped
- Visual indicators show risk level changes
- Success checkmarks confirm updates
- Modal content refreshes if viewing risk details

## Testing

### Test Scenarios
1. Map evidence via pipeline → Risk updates ✓
2. Map evidence from library → Risk updates ✓
3. Remove evidence mapping → Risk updates ✓
4. Multiple standards → Each updates independently ✓
5. Risk modal open → Content refreshes ✓

### Test File
Created `test_risk_update.html` to verify event system works correctly.

## API Integration
- Uses `/api/v1/risk/score-standard-dynamic` endpoint
- Passes standard_id and accreditor
- Receives updated risk factors including:
  - Overall risk level and score
  - Evidence coverage percentage
  - Trust score based on evidence quality
  - Staleness factor
  - Evidence metadata (count, verification status)

## Benefits
1. **Real-time Feedback**: Users see immediate impact of evidence mapping
2. **Better Decision Making**: Dynamic scores help prioritize which standards need more evidence
3. **Improved Workflow**: No need to manually refresh or re-open risk analysis
4. **Visual Clarity**: Color coding and indicators make risk levels obvious

## Next Steps
The dynamic risk analysis feature is now fully integrated and operational. Consider:
1. Adding risk trend charts to show how scores change over time
2. Email alerts when standards move to high-risk status
3. Batch risk analysis across all standards
4. Risk comparison between accreditation cycles