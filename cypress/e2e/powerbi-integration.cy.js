describe('Power BI Integration', () => {
  beforeEach(() => {
    // Login
    cy.visit('/login.html')
    cy.get('#email').type('test@example.com')
    cy.get('#password').type('testpassword123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to Power BI dashboard
    cy.visit('/powerbi-dashboard.html')
  })

  it('should load Power BI dashboard', () => {
    cy.contains('Power BI Analytics Dashboard').should('be.visible')
    cy.get('#powerBiEmbed').should('exist')
    cy.get('#reportSelector').should('be.visible')
  })

  it('should configure Power BI connection', () => {
    // Open configuration modal
    cy.get('#configurePowerBIBtn').click()
    
    // Fill in configuration
    cy.get('#tenantId').type('12345678-1234-1234-1234-123456789012')
    cy.get('#clientId').type('87654321-4321-4321-4321-210987654321')
    cy.get('#clientSecret').type('your-client-secret-here')
    cy.get('#workspaceId').type('workspace-id-123')
    
    // Test connection
    cy.get('#testConnectionBtn').click()
    cy.get('.connection-status').should('contain', 'Connected')
    
    // Save configuration
    cy.get('#saveConfigBtn').click()
    cy.get('.alert-success').should('contain', 'Configuration saved')
  })

  it('should load and display Power BI reports', () => {
    // Select a report
    cy.get('#reportSelector').select('Compliance Overview')
    cy.get('#loadReportBtn').click()
    
    // Verify report loads
    cy.get('#powerBiEmbed iframe').should('be.visible')
    cy.get('#reportTitle').should('contain', 'Compliance Overview')
  })

  it('should sync data to Power BI', () => {
    // Navigate to sync settings
    cy.get('#syncTab').click()
    
    // Configure sync settings
    cy.get('#syncFrequency').select('hourly')
    cy.get('#datasetSelector').select(['users', 'compliance_scores', 'activities'])
    
    // Map fields
    cy.get('#fieldMappingBtn').click()
    cy.get('#userIdField').select('user_id')
    cy.get('#timestampField').select('created_at')
    
    // Start sync
    cy.get('#startSyncBtn').click()
    cy.get('.sync-status').should('contain', 'Syncing')
    
    // Wait for sync to complete (mocked)
    cy.wait(2000)
    cy.get('.sync-status').should('contain', 'Completed')
    cy.get('#lastSyncTime').should('not.be.empty')
  })

  it('should create custom Power BI visuals', () => {
    // Navigate to custom visuals
    cy.get('#customVisualsTab').click()
    
    // Create new visual
    cy.get('#createVisualBtn').click()
    cy.get('#visualName').type('Department Performance Matrix')
    cy.get('#visualType').select('matrix')
    
    // Configure data
    cy.get('#rowsField').select('department')
    cy.get('#columnsField').select('month')
    cy.get('#valuesField').select('compliance_score')
    
    // Set formatting
    cy.get('#colorScheme').select('heatmap')
    cy.get('#showDataLabels').check()
    
    // Create visual
    cy.get('#generateVisualBtn').click()
    cy.get('#visualPreview').should('be.visible')
  })

  it('should schedule Power BI refresh', () => {
    // Navigate to refresh settings
    cy.get('#refreshTab').click()
    
    // Configure refresh schedule
    cy.get('#enableScheduledRefresh').check()
    cy.get('#refreshFrequency').select('daily')
    cy.get('#refreshTime').type('02:00')
    cy.get('#timeZone').select('America/New_York')
    
    // Set failure notifications
    cy.get('#notifyOnFailure').check()
    cy.get('#notificationEmail').type('admin@example.com')
    
    // Save schedule
    cy.get('#saveRefreshScheduleBtn').click()
    cy.get('.alert-success').should('contain', 'Refresh schedule saved')
  })

  it('should manage Power BI workspaces', () => {
    // Navigate to workspace management
    cy.get('#workspacesTab').click()
    
    // Create new workspace
    cy.get('#createWorkspaceBtn').click()
    cy.get('#workspaceName').type('Q4 Analytics')
    cy.get('#workspaceDescription').type('Q4 2025 departmental analytics')
    cy.get('#createBtn').click()
    
    // Verify workspace created
    cy.get('#workspacesList').should('contain', 'Q4 Analytics')
    
    // Manage workspace permissions
    cy.get('.workspace-item').contains('Q4 Analytics').within(() => {
      cy.get('.manage-permissions-btn').click()
    })
    
    cy.get('#addUserToWorkspace').type('analyst@example.com')
    cy.get('#workspaceRole').select('contributor')
    cy.get('#grantAccessBtn').click()
  })

  it('should embed Power BI dashboards', () => {
    // Get embed code
    cy.get('#getEmbedCodeBtn').click()
    
    // Configure embed settings
    cy.get('#embedType').select('secure')
    cy.get('#showNavPane').uncheck()
    cy.get('#showFilterPane').check()
    cy.get('#mobileLayout').check()
    
    // Generate embed code
    cy.get('#generateEmbedBtn').click()
    cy.get('#embedCode').should('be.visible')
    cy.get('#copyEmbedCodeBtn').click()
    cy.get('.alert-info').should('contain', 'Embed code copied')
  })

  it('should handle Power BI row-level security', () => {
    // Navigate to RLS settings
    cy.get('#securityTab').click()
    
    // Create security role
    cy.get('#createRoleBtn').click()
    cy.get('#roleName').type('Department Managers')
    cy.get('#roleFilter').type('[Department] = USERPRINCIPALNAME()')
    
    // Assign users to role
    cy.get('#addUserToRole').type('manager1@example.com')
    cy.get('#addUserBtn').click()
    cy.get('#addUserToRole').clear().type('manager2@example.com')
    cy.get('#addUserBtn').click()
    
    // Save role
    cy.get('#saveRoleBtn').click()
    cy.get('.alert-success').should('contain', 'Security role created')
  })

  it('should export Power BI data', () => {
    // Load a report first
    cy.get('#reportSelector').select('User Analytics')
    cy.get('#loadReportBtn').click()
    
    // Export data
    cy.get('#exportDataBtn').click()
    cy.get('#exportFormat').select('excel')
    cy.get('#includeFilters').check()
    cy.get('#confirmExportBtn').click()
    
    // Verify download
    cy.get('a[download*="power-bi-export"]').should('exist')
  })
})
