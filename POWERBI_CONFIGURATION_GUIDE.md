# Power BI Deep Integration Configuration Guide

## Overview
This guide helps you configure the advanced Power BI integration for MapMyStandards platform. The deep integration includes real-time embed token generation, Row-Level Security (RLS), dataset management, and comprehensive reporting capabilities.

## Required Environment Variables

Add these environment variables to your Railway deployment:

### Azure Active Directory App Registration
```bash
# Required: Azure AD Application Registration
POWERBI_CLIENT_ID=your-azure-app-client-id
POWERBI_CLIENT_SECRET=your-azure-app-client-secret  
POWERBI_TENANT_ID=your-azure-tenant-id

# Required: Power BI Workspace
POWERBI_WORKSPACE_ID=your-powerbi-workspace-guid

# Optional: For development/testing with user credentials
POWERBI_USERNAME=your-powerbi-user@domain.com
POWERBI_PASSWORD=your-powerbi-password
```

## Azure AD App Registration Setup

### Step 1: Create Azure AD Application
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in application details:
   - **Name**: MapMyStandards PowerBI Integration
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Not required for service principal auth

### Step 2: Configure API Permissions
1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Power BI Service**
3. Add these **Application permissions**:
   - `Dataset.ReadWrite.All`
   - `Report.ReadWrite.All` 
   - `Workspace.ReadWrite.All`
   - `Dashboard.ReadWrite.All`
4. Add these **Delegated permissions** (if using user auth):
   - `Dataset.Read.All`
   - `Report.Read.All`
   - `Workspace.Read.All`
5. Click **Grant admin consent**

### Step 3: Create Client Secret
1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description and set expiration
4. **Copy the secret value** - this is your `POWERBI_CLIENT_SECRET`

### Step 4: Get Application Details
- **Application (client) ID**: This is your `POWERBI_CLIENT_ID`
- **Directory (tenant) ID**: This is your `POWERBI_TENANT_ID`

## Power BI Workspace Setup

### Step 1: Create or Identify Workspace
1. Go to [Power BI Service](https://app.powerbi.com)
2. Create a new workspace or use existing one
3. Note the workspace GUID from the URL: `https://app.powerbi.com/groups/{workspace-id}/`

### Step 2: Configure Workspace Permissions
1. In Power BI workspace settings
2. Go to **Access** tab
3. Add your Azure AD application as **Admin** or **Member**
4. Use the Application (client) ID from Step 4 above

### Step 3: Enable Service Principal
1. Go to **Power BI Admin Portal** > **Tenant settings**
2. Find **Developer settings** section
3. Enable **Service principals can access Power BI APIs**
4. Add your Azure AD application to the security group

## Row-Level Security (RLS) Configuration

### Step 1: Create RLS Roles in Power BI Desktop
1. Open your report in Power BI Desktop
2. Go to **Modeling** > **Manage roles**
3. Create roles based on your institution structure:
   ```dax
   -- Institution Role
   [Institution] = USERNAME()
   
   -- Department Role  
   [Department] = LOOKUPVALUE(Users[Department], Users[Email], USERNAME())
   ```

### Step 2: Test RLS
1. Use **View as** feature in Power BI Desktop
2. Test with different user contexts
3. Verify data filtering works correctly

### Step 3: Publish to Service
1. Publish report to your configured workspace
2. In Power BI Service, go to **Security** tab
3. Add users/groups to appropriate roles

## Dataset Configuration

### Recommended Dataset Structure
```
Datasets needed for compliance reporting:
1. Compliance Metrics Dataset
   - Standards compliance scores
   - Trend data over time
   - Institution-level aggregations
   
2. Evidence Mapping Dataset
   - Document to standard mappings
   - Evidence upload tracking
   - Gap analysis data
   
3. Audit Trail Dataset
   - User activity logs
   - System changes
   - Compliance events
```

### Scheduled Refresh Setup
1. In Power BI Service, go to dataset **Settings**
2. Configure **Scheduled refresh**
3. Set appropriate frequency (recommend: every 4 hours)
4. Add gateway if using on-premises data

## Testing the Integration

### Step 1: Environment Variables Test
```bash
# Test if all variables are set
echo "Client ID: $POWERBI_CLIENT_ID"
echo "Tenant ID: $POWERBI_TENANT_ID"  
echo "Workspace ID: $POWERBI_WORKSPACE_ID"
```

### Step 2: API Test
1. Navigate to `/web/api-test.html`
2. Click **Test Config & Connection** under Power BI section
3. Verify all status indicators show green
4. Test **Get Reports** and **Get Datasets**

### Step 3: Full Integration Test
1. Navigate to `/web/powerbi-dashboard.html`
2. Check connection status panel
3. Load available reports
4. Embed a report and verify RLS works

## Security Best Practices

### Client Secret Management
- Store client secret securely in Railway environment variables
- Rotate secrets regularly (recommend: every 6 months)
- Never commit secrets to source code

### Row-Level Security
- Always implement RLS for multi-tenant scenarios
- Test RLS thoroughly with different user contexts
- Monitor for data leakage between institutions

### Token Management
- Embed tokens expire automatically (typically 1 hour)
- Implement token refresh logic for long-running sessions
- Monitor token usage and errors

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Failed to generate embed token: 401
Solution: Check client secret and app permissions
```

#### Connection Test Failed
```
Error: Connection test failed
Solution: Verify tenant ID and network connectivity
```

#### No Reports Available
```
Error: Found 0 reports
Solution: Check workspace permissions and published reports
```

#### RLS Not Working
```
Issue: Users see all data regardless of role
Solution: Verify RLS roles and username mapping
```

### Debug Tools

#### Enable Debug Logging
```python
import logging
logging.getLogger('a3e.services.powerbi_service').setLevel(logging.DEBUG)
```

#### Test Connection Manually
```python
from src.a3e.services.powerbi_service import create_powerbi_service

# Test connection
service = create_powerbi_service()
if service:
    result = await service.test_connection()
    print(f"Connection test: {result}")
```

## Production Deployment Checklist

- [ ] Azure AD app configured with proper permissions
- [ ] Client secret stored securely in Railway
- [ ] Power BI workspace permissions configured
- [ ] Service principal enabled in tenant settings
- [ ] RLS roles created and tested
- [ ] Datasets published and refresh scheduled
- [ ] API endpoints tested end-to-end
- [ ] Frontend integration verified
- [ ] Error handling and logging configured
- [ ] Security review completed

## Support Resources

- [Power BI REST API Documentation](https://docs.microsoft.com/en-us/rest/api/power-bi/)
- [Azure AD App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Power BI Embedding Guide](https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-sample-for-customers)
- [Row-Level Security Documentation](https://docs.microsoft.com/en-us/power-bi/admin/service-admin-rls)

---

**Next Steps**: After configuration, proceed to testing and then production deployment validation.
