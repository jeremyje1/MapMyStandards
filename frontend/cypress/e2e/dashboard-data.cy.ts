/// <reference types="cypress" />

const API = 'https://api.mapmystandards.ai';

describe('Dashboard data assertions', () => {
  const email = Cypress.env('E2E_EMAIL') || 'test@example.com';
  const password = Cypress.env('E2E_PASSWORD') || 'password123!';

  function loginUI() {
    cy.visit('/login');
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
  }

  it('matches readiness coverage threshold from API', () => {
    loginUI();
    cy.window().then(async (win) => {
      const res = await win.fetch(`${API}/api/user/intelligence-simple/readiness/scorecard`, {
        credentials: 'include',
        headers: { 'accept': 'application/json' },
      });
      expect(res.ok).to.equal(true);
      const body = await res.json();
      const coverage = Number(body?.coverage_percentage ?? 0);
      expect(coverage).to.be.within(0, 100);
      cy.get('[data-testid="readiness-coverage"]').invoke('text').then((txt) => {
        const uiCoverage = Number(String(txt).replace('%',''));
        expect(Math.abs(uiCoverage - coverage)).to.be.lessThan(2);
      });
      const min = Number(Cypress.env('MIN_COVERAGE') || 0);
      if (!Number.isNaN(min) && min > 0) {
        expect(coverage, `API readiness coverage >= ${min}`).to.be.gte(min);
      }
    });
  });

  it('shows non-empty review queue when API has items', () => {
    loginUI();
    cy.window().then(async (win) => {
      const res = await win.fetch(`${API}/api/user/intelligence-simple/evidence/reviews?limit=5`, {
        credentials: 'include', headers: { 'accept': 'application/json' }
      });
      expect(res.ok).to.equal(true);
      const body = await res.json();
      const items = Array.isArray(body?.items) ? body.items : (Array.isArray(body) ? body : []);
      if (items.length > 0) {
        cy.get('[data-testid="review-queue"] li').its('length').should('be.greaterThan', 0);
      } else {
        cy.get('[data-testid="review-queue"]').contains('No items in queue');
      }
    });
  });

  it('renders trend bars when timeseries available', () => {
    loginUI();
    cy.window().then(async (win) => {
      const res = await win.fetch(`${API}/api/user/intelligence-simple/metrics/timeseries`, {
        credentials: 'include', headers: { 'accept': 'application/json' }
      });
      if (res.ok) {
        cy.get('[data-testid="readiness-trend"]').find('div').its('length').should('be.greaterThan', 0);
      }
    });
  });
});
