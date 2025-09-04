describe('Team Management & RBAC', () => {
  beforeEach(() => {
    // Login as team owner
    cy.visit('/login.html')
    cy.get('#email').type('owner@example.com')
    cy.get('#password').type('ownerpass123')
    cy.get('form').submit()
    cy.url().should('include', '/dashboard')
    
    // Navigate to team settings
    cy.visit('/team-settings.html')
  })

  it('should load team settings page', () => {
    cy.contains('Team Management').should('be.visible')
    cy.get('#teamMembersTable').should('exist')
    cy.get('#inviteUserBtn').should('be.visible')
  })

  it('should invite a new team member', () => {
    // Click invite button
    cy.get('#inviteUserBtn').click()
    
    // Fill invitation form
    cy.get('#inviteEmail').type('newmember@example.com')
    cy.get('#inviteRole').select('member')
    cy.get('#inviteMessage').type('Welcome to our team!')
    cy.get('#sendInviteBtn').click()
    
    // Verify invitation sent
    cy.get('.alert-success').should('contain', 'Invitation sent')
    cy.get('#pendingInvites').should('contain', 'newmember@example.com')
  })

  it('should update team member role', () => {
    // Find existing member
    cy.get('#teamMembersTable').contains('tr', 'member@example.com').within(() => {
      cy.get('.role-select').select('admin')
      cy.get('.save-role-btn').click()
    })
    
    // Verify role updated
    cy.get('.alert-success').should('contain', 'Role updated')
    cy.get('#teamMembersTable').contains('tr', 'member@example.com')
      .should('contain', 'Admin')
  })

  it('should remove team member', () => {
    // Find member to remove
    cy.get('#teamMembersTable').contains('tr', 'toremove@example.com').within(() => {
      cy.get('.remove-member-btn').click()
    })
    
    // Confirm removal
    cy.on('window:confirm', () => true)
    
    // Verify member removed
    cy.get('.alert-success').should('contain', 'Member removed')
    cy.get('#teamMembersTable').should('not.contain', 'toremove@example.com')
  })

  it('should manage team permissions', () => {
    // Navigate to permissions tab
    cy.get('#permissionsTab').click()
    
    // Update permissions for Admin role
    cy.get('#adminPermissions').within(() => {
      cy.get('input[name="create_projects"]').should('be.checked')
      cy.get('input[name="delete_projects"]').uncheck()
      cy.get('input[name="manage_billing"]').uncheck()
    })
    
    // Save permissions
    cy.get('#savePermissionsBtn').click()
    cy.get('.alert-success').should('contain', 'Permissions updated')
  })

  it('should view audit log', () => {
    // Navigate to audit log tab
    cy.get('#auditLogTab').click()
    
    // Verify audit entries exist
    cy.get('#auditLogTable').should('exist')
    cy.get('.audit-entry').should('have.length.greaterThan', 0)
    
    // Filter audit log
    cy.get('#auditFilter').select('role_changes')
    cy.get('#applyFilterBtn').click()
    
    // Verify filtered results
    cy.get('.audit-entry').each(($el) => {
      cy.wrap($el).should('contain', 'role')
    })
  })

  it('should manage API keys', () => {
    // Navigate to API keys tab
    cy.get('#apiKeysTab').click()
    
    // Create new API key
    cy.get('#createApiKeyBtn').click()
    cy.get('#apiKeyName').type('CI/CD Integration')
    cy.get('#apiKeyScopes').select(['read', 'write'])
    cy.get('#generateKeyBtn').click()
    
    // Verify key created and copy functionality
    cy.get('.api-key-value').should('be.visible')
    cy.get('#copyApiKeyBtn').click()
    cy.get('.alert-info').should('contain', 'API key copied')
    
    // Verify key in list
    cy.get('#apiKeysList').should('contain', 'CI/CD Integration')
  })

  it('should handle team member login as different roles', () => {
    // Logout
    cy.get('#logoutBtn').click()
    
    // Login as member (limited permissions)
    cy.visit('/login.html')
    cy.get('#email').type('member@example.com')
    cy.get('#password').type('memberpass123')
    cy.get('form').submit()
    
    // Navigate to team settings
    cy.visit('/team-settings.html')
    
    // Verify limited access
    cy.get('#inviteUserBtn').should('not.exist')
    cy.get('.remove-member-btn').should('be.disabled')
    cy.get('#permissionsTab').should('not.exist')
  })

  it('should export team data', () => {
    // Click export button
    cy.get('#exportTeamDataBtn').click()
    
    // Select export options
    cy.get('#exportMembers').check()
    cy.get('#exportAuditLog').check()
    cy.get('#exportFormat').select('csv')
    cy.get('#confirmExportBtn').click()
    
    // Verify download
    cy.get('a[download*="team-export"]').should('exist')
  })
})
