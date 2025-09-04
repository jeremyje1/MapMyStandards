describe('SSO Integration', () => {
  beforeEach(() => {
    // Login as admin
    cy.visit('/login.html')
    cy.get('#email').type('admin@example.com')
    cy.get('#password').type('adminpass123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to SSO settings
    cy.visit('/sso-settings.html')
  })

  it('should load SSO settings page', () => {
    cy.contains('Single Sign-On (SSO) Configuration').should('be.visible')
    cy.get('#ssoProviderSelect').should('exist')
    cy.get('#configureSSOBtn').should('be.visible')
  })

  it('should configure SAML SSO', () => {
    // Select SAML provider
    cy.get('#ssoProviderSelect').select('saml')
    
    // Fill SAML configuration
    cy.get('#samlEntityId').type('https://example.com/saml')
    cy.get('#samlSSOUrl').type('https://idp.example.com/sso')
    cy.get('#samlCertificate').type('-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----')
    
    // Advanced settings
    cy.get('#advancedSettingsToggle').click()
    cy.get('#nameIdFormat').select('emailAddress')
    cy.get('#signRequests').check()
    
    // Save configuration
    cy.get('#saveSAMLConfigBtn').click()
    cy.get('.alert-success').should('contain', 'SAML configuration saved')
  })

  it('should configure OAuth2 SSO', () => {
    // Select OAuth2 provider
    cy.get('#ssoProviderSelect').select('oauth2')
    
    // Select specific provider
    cy.get('#oauth2Provider').select('google')
    
    // Fill OAuth2 configuration
    cy.get('#clientId').type('123456789-abcdef.apps.googleusercontent.com')
    cy.get('#clientSecret').type('GOCSPX-1234567890abcdef')
    cy.get('#redirectUri').should('have.value').and('include', '/auth/callback')
    
    // Configure scopes
    cy.get('#oauthScopes').type('email profile openid')
    
    // Save configuration
    cy.get('#saveOAuth2ConfigBtn').click()
    cy.get('.alert-success').should('contain', 'OAuth2 configuration saved')
  })

  it('should test SSO connection', () => {
    // Assume SAML is configured
    cy.get('#ssoProviderSelect').select('saml')
    
    // Click test connection
    cy.get('#testConnectionBtn').click()
    
    // Mock SSO response (in real test, would need to handle redirect)
    cy.get('#testResultModal').should('be.visible')
    cy.get('.test-status').should('contain', 'Connection successful')
    cy.get('.test-details').should('contain', 'User attributes received')
  })

  it('should map user attributes', () => {
    // Navigate to attribute mapping
    cy.get('#attributeMappingTab').click()
    
    // Configure mappings
    cy.get('#emailMapping').type('mail')
    cy.get('#firstNameMapping').type('givenName')
    cy.get('#lastNameMapping').type('sn')
    cy.get('#roleMapping').type('memberOf')
    
    // Add custom attribute
    cy.get('#addAttributeBtn').click()
    cy.get('.custom-attribute').last().find('.attr-name').type('department')
    cy.get('.custom-attribute').last().find('.attr-mapping').type('ou')
    
    // Save mappings
    cy.get('#saveAttributeMappingBtn').click()
    cy.get('.alert-success').should('contain', 'Attribute mappings saved')
  })

  it('should configure auto-provisioning', () => {
    // Navigate to provisioning tab
    cy.get('#provisioningTab').click()
    
    // Enable auto-provisioning
    cy.get('#enableAutoProvisioning').check()
    
    // Configure default role
    cy.get('#defaultRole').select('member')
    
    // Configure team assignment rules
    cy.get('#addRuleBtn').click()
    cy.get('.provisioning-rule').last().within(() => {
      cy.get('.rule-attribute').select('department')
      cy.get('.rule-operator').select('equals')
      cy.get('.rule-value').type('Engineering')
      cy.get('.rule-team').select('Engineering Team')
    })
    
    // Save provisioning settings
    cy.get('#saveProvisioningBtn').click()
    cy.get('.alert-success').should('contain', 'Provisioning settings saved')
  })

  it('should view SSO login logs', () => {
    // Navigate to logs tab
    cy.get('#ssoLogsTab').click()
    
    // Verify logs display
    cy.get('#ssoLogsTable').should('exist')
    cy.get('.log-entry').should('have.length.greaterThan', 0)
    
    // Filter logs
    cy.get('#logStatusFilter').select('failed')
    cy.get('#applyLogFilterBtn').click()
    
    // Check filtered results
    cy.get('.log-entry').each(($el) => {
      cy.wrap($el).should('contain.class', 'log-failed')
    })
  })

  it('should download SSO metadata', () => {
    // For SAML
    cy.get('#ssoProviderSelect').select('saml')
    cy.get('#downloadMetadataBtn').click()
    
    // Verify download
    cy.get('a[download*="saml-metadata.xml"]').should('exist')
  })

  it('should handle SSO login flow', () => {
    // Logout first
    cy.get('#logoutBtn').click()
    
    // Go to login page
    cy.visit('/login.html')
    
    // Click SSO login
    cy.get('#ssoLoginBtn').should('be.visible').click()
    
    // Should redirect to SSO provider
    // In real test, would need to handle external redirect
    cy.url().should('include', '/auth/sso')
  })

  it('should disable/enable SSO', () => {
    // Disable SSO
    cy.get('#ssoEnabledToggle').uncheck()
    cy.get('#confirmDisableBtn').click()
    
    // Verify disabled state
    cy.get('.sso-status').should('contain', 'Disabled')
    cy.get('#testConnectionBtn').should('be.disabled')
    
    // Re-enable SSO
    cy.get('#ssoEnabledToggle').check()
    cy.get('.sso-status').should('contain', 'Enabled')
  })
})
