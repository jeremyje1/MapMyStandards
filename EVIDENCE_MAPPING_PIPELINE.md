# Evidence Mapping Pipeline Implementation

## Summary
This document details the comprehensive evidence-mapping pipeline implemented to support accreditation preparation by mapping uploaded documents to selected standards with confidence scores and evidence excerpts.

## Key Features Implemented

### 1. Clear Workflow Navigation
- **Visual Pipeline Steps**: 5-step process clearly displayed with progress indicators
  1. Select Evidence
  2. Analyze Documents
  3. Extract Excerpts
  4. Map to Standards
  5. Review Results
- **Active Step Highlighting**: Current step is visually emphasized with scaling and color changes
- **Progress Bar**: Real-time progress tracking with smooth animations

### 2. Enhanced API Integration
- **Multiple Endpoint Support**: Fallback through multiple API endpoints for reliability
  - `/api/user/intelligence-simple/evidence/analyze`
  - `/api/user/intelligence-simple/evidence/map`
  - `/api/v1/evidence/mappings/db`
- **Real Document Analysis**: Actual document processing instead of mock data
- **Intelligent Fallbacks**: Generates smart suggestions when API is unavailable

### 3. Detailed Progress Tracking
- **Granular Status Updates**: 
  - Document-by-document analysis progress
  - Standard-by-standard mapping progress
  - Overall percentage completion
- **Activity Logs**: Timestamped logs showing each step of the process
- **Visual Indicators**: Icons and animations showing current activity

### 4. Comprehensive Results Display
- **Document Grouping**: Results organized by document for easy navigation
- **Rich Excerpt Display**:
  - Highlighted keywords in context
  - Page/location references
  - Relevance scores with visual indicators (high/medium/low)
  - Section/context information
- **Confidence Scoring**: 
  - Overall confidence badges (color-coded)
  - Individual excerpt relevance percentages
  - Mapping strength indicators

### 5. Interactive Results Management
- **Excerpt Actions**: Each excerpt can be:
  - ✓ Approved - Confirm as valid evidence
  - ✎ Edited - Refine or adjust the excerpt
  - ✗ Rejected - Remove irrelevant matches
- **Hover Effects**: Interactive UI elements with smooth transitions
- **Batch Operations**: Save all approved mappings with one click

### 6. Session Persistence
- **Mapping History**: Last 10 sessions saved locally with:
  - Timestamp
  - Document and standard counts
  - Total excerpts found
  - Average confidence score
- **Session Management**: View, load, or clear previous sessions
- **Local Storage Integration**: Quick access to recent mapping results

## User Experience Flow

1. **Initiation**
   - User clicks "Map Evidence" button
   - Modal opens showing selected standards and available evidence

2. **Evidence Selection**
   - Grid view of uploaded documents with metadata
   - Multi-select capability with visual feedback
   - File count indicator updates in real-time

3. **Mapping Process**
   - Clear status messages explaining each step
   - Progress bar shows completion percentage
   - Activity log provides detailed feedback
   - Animated icons indicate processing

4. **Results Review**
   - Summary statistics displayed prominently
   - Documents grouped with mapping counts
   - Excerpts shown with full context and highlighting
   - Interactive actions for each excerpt

5. **Completion**
   - Option to save results
   - Ability to map more evidence
   - View detailed report
   - Access mapping history

## Technical Implementation

### Progress Calculation
```javascript
let totalSteps = selectedDocs.length * (2 + selectedStandardsList.length);
let currentStep = 0;
updateProgress((currentStep / totalSteps) * 100);
```

### Keyword Highlighting
```javascript
function highlightRelevantText(text, keywords) {
    let highlighted = text;
    keywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword})`, 'gi');
        highlighted = highlighted.replace(regex, '<mark>$1</mark>');
    });
    return highlighted;
}
```

### Confidence Classification
- **High (90-100%)**: Green indicators, strong evidence
- **Medium (75-89%)**: Yellow indicators, moderate evidence  
- **Low (<75%)**: Red indicators, weak evidence

## API Response Handling

### Expected Mapping Response Structure
```json
{
  "excerpts": [
    {
      "text": "The institution maintains...",
      "section": "Policy Framework",
      "page": 12,
      "relevance_score": 0.92,
      "keywords": ["compliance", "assessment", "standards"],
      "location": {
        "page": 12,
        "paragraph": 3
      }
    }
  ],
  "overall_confidence": 0.87,
  "mapping_strength": "Strong",
  "summary": "Found strong evidence supporting this standard"
}
```

## Benefits

1. **Transparency**: Users see exactly what's happening during mapping
2. **Control**: Ability to approve/reject individual pieces of evidence
3. **Efficiency**: Batch processing of multiple documents and standards
4. **Reliability**: Multiple API fallbacks ensure consistent operation
5. **Traceability**: Complete audit trail of mapping decisions

## Future Enhancements

1. **Server-Side Persistence**: Save mapping sessions to database
2. **Collaborative Review**: Multiple users reviewing same mappings
3. **Export Capabilities**: Download mapping reports in various formats
4. **Advanced Filtering**: Filter results by confidence, document type, etc.
5. **Machine Learning**: Improve mapping accuracy based on user feedback