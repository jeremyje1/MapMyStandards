# Standards Evidence Mapping Fix

## Problem Statement
The Standards Browser listed SACSCOC standards with risk factors and weightings, and allowed selecting standards (incrementing a counter), but there was **no visible mechanism to map evidence to the selected standards or to mark them as compliant**. The "Reviewer mode" revealed assignment fields but still did not provide evidence-mapping functions.

## Solution Implemented

### 1. Evidence Mapping UI Components
**File: `web/standards-modern.html`**
- Added "Map Evidence" button to selection toolbar that appears when standards are selected
- Added "Mark Compliant" button to update compliance status of selected standards
- Created evidence selection modal with:
  - Search functionality for evidence documents
  - Grid display of available evidence with trust scores
  - Multi-select capability for mapping multiple documents

### 2. Database-Backed Evidence Mapping API
**File: `src/a3e/api/routes/evidence_mappings_db.py`**
- Created comprehensive API endpoints using SQLAlchemy database models:
  - `POST /api/v1/evidence/mappings/db` - Create evidence-to-standard mappings
  - `GET /api/v1/evidence/mappings/by-standard/{code}` - Get documents mapped to a standard
  - `GET /api/v1/evidence/mappings/db` - Get all mappings with coverage statistics
  - `GET /api/v1/evidence/coverage/heatmap/db` - Get coverage heatmap data
  - `DELETE /api/v1/evidence/mappings/db/{id}` - Remove mappings

### 3. Standards Compliance Tracking
**File: `src/a3e/api/routes/standards_compliance.py`**
- Created StandardComplianceStatus model to track compliance
- API endpoints for compliance management:
  - `POST /api/v1/standards/compliance/update` - Update compliance status
  - `GET /api/v1/standards/compliance/status/{code}` - Get compliance status
  - `GET /api/v1/standards/compliance/summary` - Get overall compliance summary

### 4. Enhanced Evidence Display
**File: `web/standards-modern.html`**
- Each standard now shows mapped evidence count and average relevance score
- Click to expand and see detailed list of mapped documents
- Visual indicators for verified documents
- Trust score display for each mapped document

## Key Features Added

1. **Evidence Mapping Workflow**:
   - Select one or more standards using checkboxes
   - Click "Map Evidence" to open document selection modal
   - Select relevant evidence documents
   - Confirm to create mappings in database

2. **Compliance Management**:
   - Select standards and click "Mark Compliant"
   - Updates compliance status based on evidence strength
   - Calculates compliance score from evidence quality

3. **Visual Feedback**:
   - Green indicators show standards with mapped evidence
   - Trust scores and verification status visible
   - Expandable details for each mapped document

4. **Database Persistence**:
   - All mappings stored in PostgreSQL database
   - Unique constraint prevents duplicate mappings
   - Tracks mapping method, confidence, and verification status

## Technical Implementation

### Database Schema
```sql
StandardMapping:
- id: UUID primary key
- document_id: Foreign key to documents
- standard_id: Foreign key to standards
- confidence_score: 0-100
- evidence_strength: Strong/Adequate/Weak
- is_verified: Boolean
- mapping_method: manual/ai_auto/verified
```

### Frontend Integration
```javascript
// Map evidence to selected standards
async function confirmEvidenceMapping() {
    // Creates mappings via /api/v1/evidence/mappings/db
}

// Mark standards as compliant
async function markStandardsCompliant() {
    // Updates status via /api/v1/standards/compliance/update
}

// Display mapped evidence
async function loadMappedEvidence(standardId) {
    // Fetches and displays mappings for each standard
}
```

## Usage Instructions

1. **Navigate to Standards Browser**
   - Go to `/standards-modern`
   - Select an accreditor (e.g., SACSCOC)

2. **Select Standards**
   - Click on standard cards to select them
   - Selection toolbar appears showing count

3. **Map Evidence**
   - Click "Map Evidence" button
   - Select relevant documents from your uploads
   - Click "Map Evidence" to confirm

4. **Mark Compliance**
   - With standards selected, click "Mark Compliant"
   - System calculates compliance score based on evidence

5. **View Mappings**
   - Look for green "evidence mapped" indicators
   - Click to expand and see document details

## Files Modified
- `web/standards-modern.html` - Added UI components and JavaScript
- `src/a3e/api/routes/evidence_mappings_db.py` - Created database-backed API
- `src/a3e/api/routes/standards_compliance.py` - Created compliance tracking API
- `src/a3e/main.py` - Registered new API routers

## Result
Users can now:
- ✅ Map evidence documents to selected standards
- ✅ Mark standards as compliant based on evidence
- ✅ View which documents support each standard
- ✅ See trust scores and verification status
- ✅ Track overall compliance progress

The platform now provides the complete evidence-to-standard mapping functionality that was advertised but previously missing.