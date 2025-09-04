describe('Advanced Reporting & Analytics', () => {
  beforeEach(() => {
    // Login
    cy.visit('/login.html')
    cy.get('#email').type('test@example.com')
    cy.get('#password').type('testpassword123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to advanced reporting
    cy.visit('/advanced-reporting.html')
  })

  it('should load the reporting dashboard', () => {
    cy.contains('Advanced Reports & Analytics').should('be.visible')
    cy.get('#reportTypeSelector').should('exist')
    cy.get('#dateRangePicker').should('exist')
    cy.get('#generateReportBtn').should('be.visible')
  })

  it('should generate usage analytics report', () => {
    // Select report type
    cy.get('#reportTypeSelector').select('usage_analytics')
    
    // Set date range
    cy.get('#startDate').type('2025-01-01')
    cy.get('#endDate').type('2025-09-04')
    
    // Select metrics
    cy.get('#metricsSelector').select(['active_users', 'page_views', 'session_duration'])
    
    // Generate report
    cy.get('#generateReportBtn').click()
    
    // Verify report generated
    cy.get('#reportContainer').should('be.visible')
    cy.get('.report-chart').should('have.length.greaterThan', 0)
    cy.get('#reportSummary').should('contain', 'Total Active Users')
  })

  it('should create custom report with filters', () => {
    // Select custom report
    cy.get('#reportTypeSelector').select('custom')
    
    // Add data sources
    cy.get('#addDataSourceBtn').click()
    cy.get('.data-source-item').last().select('user_activities')
    
    cy.get('#addDataSourceBtn').click()
    cy.get('.data-source-item').last().select('compliance_scores')
    
    // Add filters
    cy.get('#addFilterBtn').click()
    cy.get('.filter-item').last().within(() => {
      cy.get('.filter-field').select('department')
      cy.get('.filter-operator').select('equals')
      cy.get('.filter-value').type('Engineering')
    })
    
    // Configure visualization
    cy.get('#visualizationType').select('combined')
    cy.get('#chartType1').select('line')
    cy.get('#chartType2').select('bar')
    
    // Generate custom report
    cy.get('#generateReportBtn').click()
    cy.get('#customReportResults').should('be.visible')
  })

  it('should schedule recurring reports', () => {
    // Create a report first
    cy.get('#reportTypeSelector').select('compliance_summary')
    cy.get('#generateReportBtn').click()
    
    // Open scheduling modal
    cy.get('#scheduleReportBtn').click()
    
    // Configure schedule
    cy.get('#scheduleFrequency').select('weekly')
    cy.get('#scheduleDay').select('monday')
    cy.get('#scheduleTime').type('09:00')
    cy.get('#scheduleEmail').type('reports@example.com')
    
    // Additional recipients
    cy.get('#addRecipientBtn').click()
    cy.get('.recipient-email').last().type('manager@example.com')
    
    // Save schedule
    cy.get('#saveScheduleBtn').click()
    cy.get('.alert-success').should('contain', 'Report scheduled successfully')
  })

  it('should export reports in multiple formats', () => {
    // Generate a report
    cy.get('#reportTypeSelector').select('executive_summary')
    cy.get('#generateReportBtn').click()
    
    // Export as PDF
    cy.get('#exportBtn').click()
    cy.get('#exportPDF').click()
    cy.get('a[download*=".pdf"]').should('exist')
    
    // Export as Excel
    cy.get('#exportBtn').click()
    cy.get('#exportExcel').click()
    cy.get('a[download*=".xlsx"]').should('exist')
    
    // Export as CSV
    cy.get('#exportBtn').click()
    cy.get('#exportCSV').click()
    cy.get('a[download*=".csv"]').should('exist')
  })

  it('should display real-time analytics', () => {
    // Navigate to real-time tab
    cy.get('#realTimeTab').click()
    
    // Verify real-time components
    cy.get('#activeUsersCount').should('be.visible')
    cy.get('#currentActivityFeed').should('exist')
    cy.get('#liveMetricsChart').should('be.visible')
    
    // Check auto-refresh
    cy.get('#autoRefreshToggle').should('be.checked')
    cy.get('#refreshInterval').should('have.value', '30')
    
    // Verify data updates (mock WebSocket)
    cy.wait(3000)
    cy.get('#lastUpdateTime').invoke('text').should('not.be.empty')
  })

  it('should compare multiple periods', () => {
    // Select comparison report
    cy.get('#reportTypeSelector').select('period_comparison')
    
    // Set first period
    cy.get('#period1Start').type('2025-01-01')
    cy.get('#period1End').type('2025-03-31')
    
    // Set second period
    cy.get('#period2Start').type('2025-04-01')
    cy.get('#period2End').type('2025-06-30')
    
    // Add third period
    cy.get('#addPeriodBtn').click()
    cy.get('#period3Start').type('2025-07-01')
    cy.get('#period3End').type('2025-09-04')
    
    // Generate comparison
    cy.get('#generateReportBtn').click()
    
    // Verify comparison results
    cy.get('.comparison-table').should('be.visible')
    cy.get('.period-chart').should('have.length', 3)
    cy.get('#comparisonSummary').should('contain', 'Growth Rate')
  })

  it('should create dashboard from reports', () => {
    // Generate multiple reports
    cy.get('#reportTypeSelector').select('kpi_metrics')
    cy.get('#generateReportBtn').click()
    
    // Save to dashboard
    cy.get('#saveToDashboardBtn').click()
    cy.get('#dashboardName').type('Executive KPI Dashboard')
    cy.get('#widgetSize').select('medium')
    cy.get('#widgetPosition').select('top-left')
    cy.get('#createDashboardBtn').click()
    
    // Navigate to dashboards
    cy.get('#dashboardsTab').click()
    cy.get('.dashboard-list').should('contain', 'Executive KPI Dashboard')
  })

  it('should handle drill-down analytics', () => {
    // Generate summary report
    cy.get('#reportTypeSelector').select('department_overview')
    cy.get('#generateReportBtn').click()
    
    // Click on a data point to drill down
    cy.get('.chart-container').first().click(200, 150)
    
    // Verify drill-down modal
    cy.get('#drillDownModal').should('be.visible')
    cy.get('#drillDownTitle').should('contain', 'Detailed View')
    cy.get('#drillDownData').should('not.be.empty')
    
    // Further drill down
    cy.get('#drillDownTable').find('tr').first().click()
    cy.get('#secondLevelDrillDown').should('be.visible')
  })

  it('should apply AI insights to reports', () => {
    // Generate report with AI insights enabled
    cy.get('#reportTypeSelector').select('trend_analysis')
    cy.get('#enableAIInsights').check()
    cy.get('#generateReportBtn').click()
    
    // Verify AI insights section
    cy.get('#aiInsightsPanel').should('be.visible')
    cy.get('.insight-card').should('have.length.greaterThan', 0)
    cy.get('.anomaly-detection').should('exist')
    cy.get('.predictive-forecast').should('be.visible')
    
    // Interact with insights
    cy.get('.insight-action-btn').first().click()
    cy.get('#insightDetailsModal').should('be.visible')
  })
})
