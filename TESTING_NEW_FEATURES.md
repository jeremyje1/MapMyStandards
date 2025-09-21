# Testing New Features Guide

## Overview
This guide explains how to test the newly implemented Google Drive integration and webhook features that have been deployed to Railway.

## Testing Google Drive Integration

### 1. Access the Integrations Page
- Log in to your MapMyStandards account
- Navigate to: `https://your-railway-app.railway.app/integrations-management.html`

### 2. Test Google Drive OAuth
1. Click on the "Google Drive" tab
2. Click "Connect Google Drive" button
3. You'll be redirected to Google's OAuth consent page
4. Grant permissions to access your Google Drive
5. You'll be redirected back to MapMyStandards

### 3. Test Google Drive Functions
After authentication:
- **List Files**: View your Google Drive files
- **Search**: Use the search box to find specific files
- **Import**: Click "Import" on any file to add it as evidence

## Testing Webhook System

### 1. Access Webhook Management
In the integrations page, click on the "Webhooks" tab

### 2. Create a Test Webhook
1. Click "Create New Webhook"
2. Fill in:
   - **Name**: Test Webhook
   - **URL**: Use webhook.site to get a test URL
   - **Events**: Select events to monitor (e.g., standard_update, evidence_uploaded)
   - **Active**: Toggle on

### 3. Test Webhook Delivery
1. Perform an action that triggers the webhook (e.g., upload evidence)
2. Check webhook.site to see if the payload was received
3. View delivery history in the webhook management UI

## API Testing (Optional)

### Test Webhook API Endpoints
```bash
# Get your auth token first
TOKEN="your-jwt-token"

# List webhooks
curl -H "Authorization: Bearer $TOKEN" https://your-railway-app.railway.app/api/webhooks

# Create a webhook
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Test","url":"https://webhook.site/unique-url","events":["standard_update"],"active":true}' \
  https://your-railway-app.railway.app/api/webhooks

# Test webhook trigger
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://your-railway-app.railway.app/api/webhooks/{webhook_id}/test
```

### Test Google Drive API Endpoints
```bash
# Initiate OAuth
curl -H "Authorization: Bearer $TOKEN" https://your-railway-app.railway.app/api/integrations/google-drive/auth

# List files (after OAuth)
curl -H "Authorization: Bearer $TOKEN" https://your-railway-app.railway.app/api/integrations/google-drive/files

# Search files
curl -H "Authorization: Bearer $TOKEN" https://your-railway-app.railway.app/api/integrations/google-drive/search?q=evidence
```

## Monitoring Deployment

### Check Railway Logs
1. Go to Railway dashboard
2. Select your MapMyStandards app
3. View deployment logs to ensure:
   - Database migrations ran successfully
   - No import errors
   - Server started successfully

### Verify Database Tables
The following tables should exist:
- `webhook_configs` - Stores webhook configurations
- `webhook_deliveries` - Logs webhook delivery attempts

## Troubleshooting

### Google Drive Issues
- **OAuth Error**: Check Google Cloud Console for correct redirect URIs
- **File Access**: Ensure app has proper Google Drive API scopes
- **Import Fails**: Check file permissions and format

### Webhook Issues
- **Not Triggering**: Verify events are selected and webhook is active
- **Delivery Fails**: Check URL accessibility and response times
- **Missing Events**: Ensure event handlers are properly implemented

## Next Features to Implement

Based on homepage promises, these features are still pending:
1. **Team Workspaces** - Collaborative team features
2. **Predictive Analytics** - AI-powered gap prevention
3. **Full RBAC** - Role-based access control
4. **Real-time Updates** - WebSocket implementation
5. **Advanced Metrics** - Comprehensive analytics tracking

## Support
If you encounter any issues:
1. Check Railway deployment logs
2. Verify database connectivity
3. Ensure all environment variables are set correctly