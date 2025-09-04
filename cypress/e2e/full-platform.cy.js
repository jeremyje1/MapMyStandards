describe('Full Platform Integration Tests', () => {
  before(() => {
    // Setup test data
    cy.task('db:seed')
    cy.task('stripe:createTestCustomer')
  })

  after(() => {
    // Cleanup
    cy.task('db:cleanup')
    cy.task('stripe:deleteTestCustomer')
  })

  it('should complete full user journey from signup to dashboard', () => {
    // Start at homepage
    cy.visit('/')
    cy.contains('Map My Standards').should('be.visible')
    
    // Click get started
    cy.get('[data-cy=get-started]').click()
    cy.url().should('include', '/trial-signup')
    
    // Fill signup form
    cy.get('#email').type('newuser@example.com')
    cy.get('#password').type('SecurePass123!')
    cy.get('#confirmPassword').type('SecurePass123!')
    cy.get('#organizationName').type('Test University')
    cy.get('#agreeTerms').check()
    
    // Submit and go to payment
    cy.get('#signupBtn').click()
    cy.url().should('include', '/checkout')
    
    // Enter payment details (using Stripe test card)
    cy.get('iframe[name*="__privateStripeFrame"]').then($iframe => {
      const body = $iframe.contents().find('body')
      cy.wrap(body)
        .find('input[name="cardnumber"]')
        .type('4242424242424242')
      cy.wrap(body)
        .find('input[name="exp-date"]')
        .type('1234')
      cy.wrap(body)
        .find('input[name="cvc"]')
        .type('123')
      cy.wrap(body)
        .find('input[name="postal"]')
        .type('12345')
    })
    
    // Complete payment
    cy.get('#completePaymentBtn').click()
    
    // Should redirect to onboarding
    cy.url().should('include', '/onboarding')
    cy.contains('Welcome to Map My Standards').should('be.visible')
    
    // Complete onboarding
    cy.get('#institutionType').select('university')
    cy.get('#accreditingBody').select('HLC')
    cy.get('#primaryContact').type('John Doe')
    cy.get('#nextBtn').click()
    
    // Skip optional steps
    cy.get('#skipBtn').click()
    cy.get('#finishOnboardingBtn').click()
    
    // Should arrive at dashboard
    cy.url().should('include', '/dashboard')
    cy.contains('Dashboard').should('be.visible')
    cy.get('#welcomeMessage').should('contain', 'Test University')
  })

  it('should handle team collaboration workflow', () => {
    // Login as owner
    cy.login('owner@example.com', 'ownerpass')
    
    // Create team and invite member
    cy.visit('/team-settings.html')
    cy.get('#inviteUserBtn').click()
    cy.get('#inviteEmail').type('teammate@example.com')
    cy.get('#inviteRole').select('admin')
    cy.get('#sendInviteBtn').click()
    
    // Logout and accept invitation
    cy.logout()
    cy.task('email:getLatestInvite').then((inviteLink) => {
      cy.visit(inviteLink)
    })
    
    // Complete signup for invited user
    cy.get('#password').type('TeamPass123!')
    cy.get('#confirmPassword').type('TeamPass123!')
    cy.get('#acceptInviteBtn').click()
    
    // Verify team access
    cy.url().should('include', '/dashboard')
    cy.get('#teamName').should('be.visible')
    
    // Create shared org chart
    cy.visit('/org-chart.html')
    cy.get('#addNodeBtn').click()
    cy.get('#nodeTitle').type('Shared Department')
    cy.get('#createNodeBtn').click()
    cy.get('#saveChartBtn').click()
    
    // Switch to owner account and verify
    cy.logout()
    cy.login('owner@example.com', 'ownerpass')
    cy.visit('/org-chart.html')
    cy.get('#orgChartContainer').should('contain', 'Shared Department')
  })

  it('should integrate all features in a workflow', () => {
    cy.login('test@example.com', 'testpass')
    
    // 1. Create organization structure
    cy.visit('/org-chart.html')
    cy.createDepartment('Academic Affairs')
    cy.createDepartment('Student Services')
    cy.createDepartment('Administration')
    
    // 2. Run scenario modeling
    cy.visit('/scenario-modeling.html')
    cy.get('#scenarioName').type('Accreditation Preparation')
    cy.get('#initialInvestment').type('50000')
    cy.get('#monthlyRevenue').type('10000')
    cy.get('#calculateBtn').click()
    cy.get('#saveScenarioBtn').click()
    
    // 3. Configure Power BI
    cy.visit('/powerbi-dashboard.html')
    cy.get('#reportSelector').select('Accreditation Progress')
    cy.get('#loadReportBtn').click()
    
    // 4. Generate report
    cy.visit('/advanced-reporting.html')
    cy.get('#reportTypeSelector').select('accreditation_readiness')
    cy.get('#generateReportBtn').click()
    cy.get('#exportPDF').click()
    
    // 5. Share with team
    cy.visit('/team-settings.html')
    cy.get('#shareReportBtn').click()
    cy.get('#shareWithTeam').check()
    cy.get('#sendReportBtn').click()
    
    // Verify integration
    cy.visit('/dashboard.html')
    cy.get('#recentActivity').should('contain', 'Accreditation Preparation')
    cy.get('#teamNotifications').should('contain', 'New report shared')
  })

  it('should handle error scenarios gracefully', () => {
    cy.login('test@example.com', 'testpass')
    
    // Test API error handling
    cy.intercept('POST', '/api/scenarios', { statusCode: 500 })
    cy.visit('/scenario-modeling.html')
    cy.get('#scenarioName').type('Error Test')
    cy.get('#calculateBtn').click()
    cy.get('.alert-danger').should('contain', 'error occurred')
    
    // Test network offline
    cy.intercept('GET', '/api/**', { forceNetworkError: true })
    cy.visit('/dashboard.html')
    cy.get('.offline-banner').should('be.visible')
    
    // Test validation errors
    cy.visit('/team-settings.html')
    cy.get('#inviteUserBtn').click()
    cy.get('#inviteEmail').type('invalid-email')
    cy.get('#sendInviteBtn').click()
    cy.get('.validation-error').should('contain', 'valid email')
  })

  it('should maintain data consistency across features', () => {
    cy.login('test@example.com', 'testpass')
    
    // Create data in one feature
    const departmentName = `Test Dept ${Date.now()}`
    cy.visit('/org-chart.html')
    cy.createDepartment(departmentName)
    
    // Verify it appears in reporting
    cy.visit('/advanced-reporting.html')
    cy.get('#reportTypeSelector').select('department_overview')
    cy.get('#generateReportBtn').click()
    cy.get('#reportContent').should('contain', departmentName)
    
    // Verify in Power BI
    cy.visit('/powerbi-dashboard.html')
    cy.get('#datasetRefreshBtn').click()
    cy.wait(2000)
    cy.get('#departmentsList').should('contain', departmentName)
    
    // Delete and verify removal
    cy.visit('/org-chart.html')
    cy.deleteDepartment(departmentName)
    cy.visit('/advanced-reporting.html')
    cy.get('#generateReportBtn').click()
    cy.get('#reportContent').should('not.contain', departmentName)
  })
})
