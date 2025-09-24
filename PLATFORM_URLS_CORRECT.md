# Platform URLs - Correct Configuration 🌐

## Production Environment URLs

### Marketing Site (WordPress)
- **URL**: https://mapmystandards.ai
- **Purpose**: Marketing, landing page, product information
- **Platform**: WordPress

### Application Platform (Frontend)
- **URL**: https://platform.mapmystandards.ai
- **Purpose**: The actual web application where users interact
- **Platform**: Vercel (static hosting)
- **Repository**: `/web` directory

### API Backend
- **URL**: https://api.mapmystandards.ai
- **Purpose**: REST API endpoints
- **Platform**: Railway (Python FastAPI)
- **Repository**: `/src/a3e` directory

## Key Application Pages

### Enhanced Pages (Live on Platform)
1. **Dashboard**: https://platform.mapmystandards.ai/dashboard-enhanced
2. **Upload (NEW)**: https://platform.mapmystandards.ai/upload-enhanced-v2
3. **Standards Graph**: https://platform.mapmystandards.ai/standards-graph-enhanced
4. **Reports**: https://platform.mapmystandards.ai/reports-enhanced
5. **Settings**: https://platform.mapmystandards.ai/settings-enhanced
6. **About**: https://platform.mapmystandards.ai/about-enhanced
7. **Contact**: https://platform.mapmystandards.ai/contact-enhanced
8. **Compliance Dashboard**: https://platform.mapmystandards.ai/compliance-dashboard-enhanced
9. **Organizational**: https://platform.mapmystandards.ai/organizational-enhanced

### API Endpoints (Enhanced Upload)
- **Upload Document**: `POST https://api.mapmystandards.ai/api/documents/upload`
- **List Documents**: `GET https://api.mapmystandards.ai/api/documents`
- **Download Document**: `GET https://api.mapmystandards.ai/api/documents/{id}/download`
- **Delete Document**: `DELETE https://api.mapmystandards.ai/api/documents/{id}`
- **Check Notifications**: `GET https://api.mapmystandards.ai/api/documents/notifications`

## Test Credentials
- **Email**: jeremy@mapmystandards.com
- **Password**: Test123!@#

## Features Implemented in Upload V2
✅ S3 file storage integration
✅ Drag & drop upload interface
✅ Real-time upload progress bars
✅ Toast notifications system
✅ Document listing with metadata
✅ Download/delete functionality
✅ Loading indicators for async operations
✅ Category selection for documents
✅ File type and size validation

## Common Confusion Points
❌ **WRONG**: https://mapmystandards.ai/upload-enhanced-v2.html (This is the WordPress site)
✅ **CORRECT**: https://platform.mapmystandards.ai/upload-enhanced-v2 (This is the app)

## Deployment Commands
- **Frontend**: `cd /web && vercel --prod`
- **Backend**: Automatically deployed via Railway on git push

## Important Notes
1. The WordPress site (mapmystandards.ai) is for marketing only
2. All application functionality is on platform.mapmystandards.ai
3. The API is always accessed via api.mapmystandards.ai
4. Vercel routes automatically strip .html extensions