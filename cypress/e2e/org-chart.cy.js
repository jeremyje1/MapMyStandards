describe('Organization Chart', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/login.html')
    cy.get('#email').type('test@example.com')
    cy.get('#password').type('testpassword123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to org chart
    cy.visit('/org-chart.html')
  })

  it('should load the org chart page', () => {
    cy.contains('Organization Hierarchy').should('be.visible')
    cy.get('#orgChartContainer').should('exist')
    cy.get('#addNodeBtn').should('be.visible')
  })

  it('should add a new department node', () => {
    // Click add node button
    cy.get('#addNodeBtn').click()
    
    // Fill in the modal
    cy.get('#nodeTitle').type('Engineering Department')
    cy.get('#nodeType').select('department')
    cy.get('#nodeDescription').type('Software development team')
    cy.get('#createNodeBtn').click()
    
    // Verify node was added
    cy.get('#orgChartContainer').should('contain', 'Engineering Department')
  })

  it('should edit an existing node', () => {
    // First add a node
    cy.get('#addNodeBtn').click()
    cy.get('#nodeTitle').type('HR Department')
    cy.get('#nodeType').select('department')
    cy.get('#createNodeBtn').click()
    
    // Click on the node to edit
    cy.get('.vis-network').click(200, 200) // Approximate location
    cy.get('#editNodeBtn').should('be.visible').click()
    
    // Update the node
    cy.get('#nodeTitle').clear().type('Human Resources')
    cy.get('#updateNodeBtn').click()
    
    // Verify update
    cy.get('#orgChartContainer').should('contain', 'Human Resources')
  })

  it('should delete a node', () => {
    // Add a node first
    cy.get('#addNodeBtn').click()
    cy.get('#nodeTitle').type('Temp Department')
    cy.get('#createNodeBtn').click()
    
    // Select and delete
    cy.get('.vis-network').click(200, 200)
    cy.get('#deleteNodeBtn').click()
    
    // Confirm deletion
    cy.on('window:confirm', () => true)
    
    // Verify deletion
    cy.get('#orgChartContainer').should('not.contain', 'Temp Department')
  })

  it('should save and load org chart', () => {
    // Add some nodes
    cy.get('#addNodeBtn').click()
    cy.get('#nodeTitle').type('Sales Team')
    cy.get('#createNodeBtn').click()
    
    // Save chart
    cy.get('#saveChartBtn').click()
    cy.get('.alert-success').should('contain', 'saved successfully')
    
    // Reload page
    cy.reload()
    
    // Verify chart persisted
    cy.get('#orgChartContainer').should('contain', 'Sales Team')
  })

  it('should export org chart as image', () => {
    // Add a node
    cy.get('#addNodeBtn').click()
    cy.get('#nodeTitle').type('Marketing')
    cy.get('#createNodeBtn').click()
    
    // Export as image
    cy.get('#exportImageBtn').click()
    
    // Verify download initiated (check for download attribute)
    cy.get('a[download*="org-chart"]').should('exist')
  })

  it('should handle real-time collaboration', () => {
    // This would require WebSocket mocking or a test server
    // For now, just verify the UI elements exist
    cy.get('#collaboratorsList').should('exist')
    cy.get('#shareChartBtn').should('be.visible')
  })
})
