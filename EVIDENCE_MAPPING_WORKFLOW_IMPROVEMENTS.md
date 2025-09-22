# Evidence Mapping Workflow Improvements

## Summary
This document outlines the improvements made to address the unclear evidence-mapping workflow issue. The enhancements create a consistent, intuitive pathway from uploading evidence to mapping it against standards, making the core value proposition of "real-time mapping" accessible and visible.

## Issues Addressed
- No clear pathway from evidence upload to mapping
- Missing "map evidence" visual cues after file upload
- Lack of status indicators showing mapping progress
- Unclear connection between uploaded files and standards

## Improvements Implemented

### 1. Evidence Upload Status Banner
- **New Component**: Added a prominent evidence status banner that appears after files are uploaded
- **Location**: Displays between workflow progress and standards list
- **Features**:
  - Shows all uploaded evidence files in a grid layout
  - Visual status indicators for each file (unmapped ❌, mapping in progress ⏳, mapped ✅)
  - Individual "Map to Standards" button for each unmapped file
  - Global "Map All to Standards" button for bulk mapping

### 2. Visual Status Indicators
- **Three States**: 
  - Unmapped (red ❌) - File uploaded but not yet linked to standards
  - Mapping (animated yellow ⏳) - AI analysis in progress
  - Mapped (green ✅) - Successfully linked to standards
- **Real-time Updates**: Status changes immediately when mapping starts/completes
- **Persistent State**: Mapping status saved in localStorage for consistency

### 3. Enhanced Workflow Steps
- **Tooltips Added**: Each workflow step now shows helpful hints on hover
- **Clear Actions**: Clicking workflow steps triggers appropriate actions
- **Visual Progress**: Steps show completed/active/pending states clearly

### 4. Individual File Mapping
- **Per-File Actions**: Each uploaded file has its own "Map to Standards" button
- **Pre-selection**: Clicking maps just that specific file
- **Status Feedback**: Button changes to "Mapping..." during process

### 5. Mapping Results Display
- **Success Summary**: After mapping completes, a summary banner shows:
  - Total standards linked
  - Files mapped to each standard
  - Confidence scores for each mapping
- **Auto-dismiss**: Summary disappears after 30 seconds or can be manually dismissed
- **Clear Connections**: Shows which documents support which standards

### 6. Real-time Progress Feedback
- **During Mapping**:
  - Files show "Mapping in Progress..." status
  - Animated loading indicator
  - Map button disabled to prevent duplicate requests
- **After Completion**:
  - Status updates to "Successfully mapped"
  - Button replaced with success message
  - Evidence banner refreshes to show new status

## Code Changes

### CSS Additions
```css
/* Evidence Upload Status Banner */
.evidence-upload-banner { /* Styles for the main banner */ }
.evidence-files-grid { /* Grid layout for evidence files */ }
.evidence-file-card { /* Individual file card styling */ }
.evidence-mapping-status-indicator { /* Status indicator styles */ }
.status-unmapped, .status-mapping, .status-mapped { /* State colors */ }
.map-file-button { /* Individual map button styles */ }

/* Mapping Results Summary */
.mapping-results-summary { /* Success summary styling */ }
.mapping-results-grid { /* Results grid layout */ }
.mapping-confidence-score { /* Confidence score badges */ }
```

### JavaScript Functions Added
1. **`displayEvidenceUploadStatus()`** - Shows uploaded files with mapping status
2. **`getEvidenceMappingStatus(files)`** - Retrieves mapping status for files
3. **`mapSingleFile(filename)`** - Maps individual file to standards
4. **`updateFileStatus(filename, status)`** - Updates UI status for a file
5. **`displayMappingResultsSummary(results, savedCount)`** - Shows mapping success summary

### HTML Additions
- Evidence upload status banner section
- Enhanced workflow step tooltips
- Mapping results summary container

## User Experience Flow

### Before Improvements
1. User uploads evidence → No clear next step
2. "Map Evidence" button exists but connection unclear
3. No feedback on mapping status
4. Results not clearly displayed

### After Improvements
1. User uploads evidence → Evidence banner appears immediately
2. Each file shows clear unmapped status with action button
3. Click "Map to Standards" → Status changes to "mapping in progress"
4. Mapping completes → Status updates to "mapped" + results summary
5. Clear visual feedback throughout entire process

## Benefits
1. **Intuitive Workflow**: Clear visual path from upload to mapping
2. **Real-time Feedback**: Users see exactly what's happening
3. **Individual Control**: Can map files one at a time or all at once
4. **Progress Visibility**: No more guessing about mapping status
5. **Results Clarity**: Clear display of which files support which standards

## Testing Recommendations
1. Upload multiple evidence files
2. Map individual files and verify status updates
3. Use "Map All" button for bulk operations
4. Check persistence of mapping status across page reloads
5. Verify mapping results summary displays correctly

## Future Enhancements
1. Add mapping queue for handling many files
2. Show mapping progress percentage
3. Allow re-mapping of already mapped files
4. Add filters to show only unmapped/mapped files
5. Export mapping results as a report