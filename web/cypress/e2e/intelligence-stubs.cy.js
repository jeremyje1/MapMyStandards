describe('AI Readiness intelligence stubs', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/v1/feature-flags', {
      standards_graph: true,
      evidence_mapper: true,
      evidence_trust_score: true,
      gap_risk_predictor: true,
      crosswalkx: true,
      citeguard: true,
    }).as('featureFlags');

    cy.intercept('GET', '/api/v1/intelligence/standards-graph', {
      graph: { nodes: [{ id: 'a', label: 'Institution', type: 'institution' }], edges: [] },
      metadata: {},
    }).as('standardsGraph');

    cy.intercept('GET', '/api/v1/intelligence/evidence-mapper', {
      mappings: [{ evidence_id: 'doc-1', standard_id: 'STD-1', alignment: 'strong' }],
      summary: {},
    }).as('evidenceMapper');

    cy.intercept('GET', '/api/v1/intelligence/evidence-trust', {
      documents: [{ id: 'doc-1', title: 'Policy', trust_score: 0.92 }],
      methodology: {},
    }).as('evidenceTrust');

    cy.intercept('GET', '/api/v1/intelligence/gap-risk', {
      risk_profile: { overall_risk: 'low', drivers: [] },
      timeline: [],
    }).as('gapRisk');

    cy.intercept('GET', '/api/v1/intelligence/crosswalkx', {
      matches: [{ source: 'MSCHE 1.1', target: 'HLC 1.A', confidence: 0.87 }],
      unmatched_source: [],
      unmatched_target: [],
    }).as('crosswalk');

    cy.intercept('GET', '/api/v1/intelligence/citeguard', {
      issues: [{ citation: 'Standard 3', status: 'missing', recommendation: 'Add reference' }],
      summary: {},
    }).as('citeguard');

    cy.visit('/ai-readiness-suite.html');
  });

  it('shows standards graph data', () => {
    cy.wait('@standardsGraph');
    cy.get('#standardsGraphData li').should('have.length', 1);
  });

  it('renders evidence mapper summary', () => {
    cy.wait('@evidenceMapper');
    cy.contains('#evidenceMapperData li', 'STD-1').should('exist');
  });

  it('displays trust score', () => {
    cy.wait('@evidenceTrust');
    cy.contains('#evidenceTrustData li', '92%').should('exist');
  });

  it('presents gap risk panel', () => {
    cy.wait('@gapRisk');
    cy.contains('#gapRiskData', 'Overall risk');
  });

  it('lists crosswalk matches', () => {
    cy.wait('@crosswalk');
    cy.contains('#crosswalkData li', 'HLC 1.A');
  });

  it('shows citeguard issues', () => {
    cy.wait('@citeguard');
    cy.contains('#citeguardData li', 'missing');
  });
});
