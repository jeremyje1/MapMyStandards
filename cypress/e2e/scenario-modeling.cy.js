describe('Scenario Modeling & ROI Calculator', () => {
  beforeEach(() => {
    // Login
    cy.visit('/login.html')
    cy.get('#email').type('test@example.com')
    cy.get('#password').type('testpassword123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to scenario modeling
    cy.visit('/scenario-modeling.html')
  })

  it('should load the scenario modeling page', () => {
    cy.contains('Scenario Modeling & ROI Calculator').should('be.visible')
    cy.get('#scenarioForm').should('exist')
    cy.get('#roiChart').should('exist')
  })

  it('should calculate basic ROI', () => {
    // Fill in scenario details
    cy.get('#scenarioName').type('Digital Transformation Project')
    cy.get('#initialInvestment').clear().type('50000')
    cy.get('#timeframe').clear().type('12')
    cy.get('#monthlyRevenue').clear().type('8000')
    cy.get('#monthlyCosts').clear().type('2000')
    
    // Calculate ROI
    cy.get('#calculateBtn').click()
    
    // Verify results
    cy.get('#roiResult').should('be.visible')
    cy.get('#paybackPeriod').should('contain', 'months')
    cy.get('#netPresentValue').should('exist')
    cy.get('#internalRateReturn').should('exist')
  })

  it('should add multiple cost/benefit items', () => {
    cy.get('#scenarioName').type('Cost Reduction Initiative')
    
    // Add costs
    cy.get('#addCostBtn').click()
    cy.get('.cost-item').last().find('.cost-name').type('Software Licenses')
    cy.get('.cost-item').last().find('.cost-amount').type('5000')
    
    cy.get('#addCostBtn').click()
    cy.get('.cost-item').last().find('.cost-name').type('Training')
    cy.get('.cost-item').last().find('.cost-amount').type('3000')
    
    // Add benefits
    cy.get('#addBenefitBtn').click()
    cy.get('.benefit-item').last().find('.benefit-name').type('Productivity Gains')
    cy.get('.benefit-item').last().find('.benefit-amount').type('15000')
    
    // Calculate
    cy.get('#calculateBtn').click()
    cy.get('#totalCosts').should('contain', '8000')
    cy.get('#totalBenefits').should('contain', '15000')
  })

  it('should save and load scenarios', () => {
    // Create scenario
    cy.get('#scenarioName').type('Expansion Plan 2025')
    cy.get('#initialInvestment').type('100000')
    cy.get('#monthlyRevenue').type('20000')
    
    // Save scenario
    cy.get('#saveScenarioBtn').click()
    cy.get('.alert-success').should('contain', 'Scenario saved')
    
    // Load scenarios list
    cy.get('#loadScenarioBtn').click()
    cy.get('.scenario-list').should('contain', 'Expansion Plan 2025')
    
    // Load the scenario
    cy.get('.scenario-list-item').contains('Expansion Plan 2025').click()
    cy.get('#scenarioName').should('have.value', 'Expansion Plan 2025')
    cy.get('#initialInvestment').should('have.value', '100000')
  })

  it('should compare multiple scenarios', () => {
    // Create first scenario
    cy.get('#scenarioName').type('Option A')
    cy.get('#initialInvestment').type('50000')
    cy.get('#monthlyRevenue').type('10000')
    cy.get('#saveScenarioBtn').click()
    
    // Create second scenario
    cy.get('#newScenarioBtn').click()
    cy.get('#scenarioName').type('Option B')
    cy.get('#initialInvestment').type('30000')
    cy.get('#monthlyRevenue').type('7000')
    cy.get('#saveScenarioBtn').click()
    
    // Compare scenarios
    cy.get('#compareBtn').click()
    cy.get('#comparisonModal').should('be.visible')
    cy.get('.comparison-chart').should('exist')
    cy.get('.scenario-comparison').should('contain', 'Option A')
    cy.get('.scenario-comparison').should('contain', 'Option B')
  })

  it('should export scenario report', () => {
    // Create scenario
    cy.get('#scenarioName').type('Q4 Investment Plan')
    cy.get('#initialInvestment').type('75000')
    cy.get('#calculateBtn').click()
    
    // Export options
    cy.get('#exportBtn').click()
    cy.get('#exportPDF').click()
    
    // Verify download (check for download attribute)
    cy.get('a[download*="scenario-report"]').should('exist')
  })

  it('should update charts in real-time', () => {
    // Enter initial values
    cy.get('#initialInvestment').type('40000')
    cy.get('#monthlyRevenue').type('5000')
    
    // Verify chart updates
    cy.get('#roiChart canvas').should('exist')
    
    // Change values and verify chart updates
    cy.get('#monthlyRevenue').clear().type('8000')
    cy.get('#calculateBtn').click()
    
    // Chart should reflect new values
    cy.get('#roiChart').should('be.visible')
  })

  it('should handle sensitivity analysis', () => {
    // Set base scenario
    cy.get('#scenarioName').type('Base Case')
    cy.get('#initialInvestment').type('60000')
    cy.get('#monthlyRevenue').type('12000')
    
    // Enable sensitivity analysis
    cy.get('#sensitivityToggle').click()
    
    // Adjust sensitivity parameters
    cy.get('#revenueVariation').type('20') // +/- 20%
    cy.get('#costVariation').type('15') // +/- 15%
    
    // Run analysis
    cy.get('#runSensitivityBtn').click()
    
    // Verify results
    cy.get('#sensitivityResults').should('be.visible')
    cy.get('.best-case-roi').should('exist')
    cy.get('.worst-case-roi').should('exist')
    cy.get('.most-likely-roi').should('exist')
  })
})
