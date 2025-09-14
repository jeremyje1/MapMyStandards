describe('Single Plan Subscription Flow', () => {
  beforeEach(() => {
    // Visit the homepage
    cy.visit('https://platform.mapmystandards.ai')
  })

  it('should display $199/month pricing on homepage', () => {
    // Check that the pricing section shows $199
    cy.contains('$199').should('be.visible')
    cy.contains('/month').should('be.visible')
    cy.contains('Full platform access').should('be.visible')
  })

  it('should allow authenticated user to access all features', () => {
    // Mock authentication
    cy.window().then((win) => {
      win.localStorage.setItem('auth_token', 'mock_token')
      win.localStorage.setItem('subscription_status', 'active')
    })

    // Visit dashboard
  cy.visit('https://platform.mapmystandards.ai/ai-dashboard.html')
    
    // Check that all features are accessible (no tier restrictions)
    cy.contains('Complete Setup').should('be.visible')
    
    // Verify onboarding link exists
    cy.get('a[href="/onboarding"]').should('exist')
  })

  it('should redirect to single plan checkout', () => {
    // Click on start trial or subscribe button
    cy.contains('Start 7-Day Free Trial').click()
    
    // Should navigate to trial signup
    cy.url().should('include', 'trial-signup')
    
    // Verify single plan is presented
    cy.contains('$199/month after trial').should('be.visible')
  })

  it('should show all features included in single plan', () => {
    // Navigate to pricing section
    cy.get('a[href="#pricing"]').click()
    
    // Verify all features are listed
    const features = [
      'Evidence Mapping',
      'Narrative Generation',
      'Gap Risk Prediction',
      'Unlimited Users'
    ]
    
    features.forEach(feature => {
      cy.contains(feature).should('be.visible')
    })
  })
})
