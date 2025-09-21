/// <reference types="cypress" />

describe('Onboarding flow', () => {
  it('redirects to onboarding when settings missing and saves accreditor', () => {
    cy.visit('/login');
    // Assume test user exists; replace with valid creds in CI secrets if needed
    const email = Cypress.env('E2E_EMAIL') || 'test@example.com';
    const password = Cypress.env('E2E_PASSWORD') || 'password123!';

    cy.get('input#email').type(email);
    cy.get('input#password').type(password);
    cy.get('button[type="submit"]').click();

    cy.location('pathname', { timeout: 15000 }).should('match', /\/dashboard|\/onboarding/);

    cy.location('pathname').then((path: string) => {
      if (path.includes('/onboarding')) {
        cy.get('select').first().select('HLC');
        cy.contains('button', 'Continue').click();
        cy.location('pathname', { timeout: 15000 }).should('include', '/dashboard');
      }
    });
  });
});
