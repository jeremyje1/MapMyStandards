/// <reference types="cypress" />

describe('Standards checklist happy path', () => {
  it('loads checklist and shows coverage', () => {
    cy.visit('/login');
    const email = Cypress.env('E2E_EMAIL') || 'test@example.com';
    const password = Cypress.env('E2E_PASSWORD') || 'password123!';

    cy.get('input#email').type(email);
    cy.get('input#password').type(password);
    cy.get('button[type="submit"]').click();

    cy.location('pathname', { timeout: 15000 }).should('match', /\/dashboard|\/onboarding/);

    // If onboarding appears, continue and go to standards
    cy.location('pathname').then((path: string) => {
      if (path.includes('/onboarding')) {
        cy.get('select').first().select('HLC');
        cy.contains('button', 'Continue').click();
      }
    });

    cy.contains('a', 'Standards').click();
    cy.location('pathname', { timeout: 15000 }).should('include', '/standards');

    // Coverage shows a percentage
    cy.contains('Checklist Coverage');
    cy.get('div').contains('%');
  });
});
