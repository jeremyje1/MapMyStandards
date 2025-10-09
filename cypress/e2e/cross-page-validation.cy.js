const apiPayloads = {
  metrics: {
    core_metrics: {
      documents_analyzed: 5,
      standards_mapped: 7,
      total_standards: 10,
    },
    performance_metrics: {
      coverage_percentage: 72.5,
      compliance_score: 80.1,
      average_trust: 0.78,
    },
    account_info: {
      institution_name: 'Test University',
      primary_accreditor: 'HLC',
    },
  },
  evidenceMap: {
    counts: {
      documents: 5,
      standards_mapped: 7,
      total_standards: 10,
    },
    coverage_percentage: 72.5,
    mapping: {
      'HLC.1.A': [{ confidence: 0.82 }],
    },
    standards: [
      { standard_id: 'HLC.1.A', avg_confidence: 0.82, evidence_count: 1 },
      { standard_id: 'HLC.1.B', avg_confidence: 0.77, evidence_count: 2 },
    ],
  },
  gapAnalysis: {
    gap_analysis: {
      total_gaps: 3,
      high_risk: 1,
      medium_risk: 1,
      low_risk: 1,
      gaps: [
        {
          id: 'G1',
          risk_level: 'High',
          title: 'Policy Coverage',
          risk_score: 0.82,
          recommendation: 'Upload updated policy evidence.',
          standard: {
            code: 'HLC.1.A',
            title: 'Mission and Integrity',
          },
        },
        {
          id: 'G2',
          risk_level: 'Medium',
          title: 'Assessment Frequency',
          risk_score: 0.6,
          recommendation: 'Provide additional assessment documentation.',
          standard: {
            code: 'HLC.2.B',
            title: 'Teaching and Learning',
          },
        },
        {
          id: 'G3',
          risk_level: 'Low',
          title: 'Documentation',
          risk_score: 0.3,
          recommendation: 'Maintain evidence library updates.',
          standard: {
            code: 'HLC.3.C',
            title: 'Resources and Planning',
          },
        },
      ],
      recommendations: [
        { id: 'R1', priority: 'High', summary: 'Focus on mission-aligned evidence.' },
      ],
    },
  },
  crosswalk: {
    reuse_percentage: 45,
    multi_use_count: 1,
    matrix: {
      'artifact-1.pdf': {
        'HLC.1.A': { accreditor: 'HLC' },
        'SACS.1.B': { accreditor: 'SACS' },
      },
    },
  },
};

function inlineMetricsStore(html) {
  if (!/metrics-store\.js/.test(html)) {
    return cy.wrap(html);
  }
  return cy.readFile('web/js/metrics-store.js', { log: false }).then((storeSource) =>
    html.replace(/<script\s+src=["']\/?js\/metrics-store\.js[^>]*><\/script>/g, `<script>${storeSource}</script>`)
  );
}

function serveStaticPage(page, { query = '', onBeforeLoad } = {}) {
  return cy
    .readFile(`web/${page}`, { log: false })
    .then((html) => inlineMetricsStore(html))
    .then((inlined) => {
      cy.intercept('GET', `**/${page}*`, (req) => {
        req.reply(inlined);
      }).as(`${page}-html`);

      return cy.visit(`/${page}${query}`, {
        onBeforeLoad(win) {
          if (onBeforeLoad) {
            onBeforeLoad(win);
          }
        },
      });
    });
}

function installApiStub(win, overrides = {}) {
  const payloads = { ...apiPayloads, ...overrides };
  win.localStorage.setItem('access_token', 'test-token');
  win.__fetchHits = {};

  function respond(body) {
    const jsonString = JSON.stringify(body ?? {});
    return Promise.resolve({
      ok: true,
      status: 200,
      text: async () => jsonString,
      json: async () => body ?? {},
    });
  }

  const resolver = (url = '') => {
    if (url.includes('/dashboard/metrics')) {
      win.__fetchHits.metrics = (win.__fetchHits.metrics || 0) + 1;
      return respond(payloads.metrics);
    }
    if (url.includes('/standards/evidence-map')) {
      win.__fetchHits.evidenceMap = (win.__fetchHits.evidenceMap || 0) + 1;
      return respond(payloads.evidenceMap);
    }
    if (url.includes('/gaps/analysis')) {
      win.__fetchHits.gaps = (win.__fetchHits.gaps || 0) + 1;
      return respond(payloads.gapAnalysis);
    }
    if (url.includes('/evidence/crosswalk')) {
      win.__fetchHits.crosswalk = (win.__fetchHits.crosswalk || 0) + 1;
      return respond(payloads.crosswalk);
    }
    if (url.includes('/user/profile')) {
      return respond({
        organization: 'Test University',
        institution_name: 'Test University',
        documents_analyzed: 5,
        primary_accreditor: 'HLC',
        reports_generated: 1,
      });
    }
    if (url.includes('/settings')) {
      return respond({});
    }
    if (url.includes('/uploads')) {
      return respond([]);
    }
    throw new Error(`Unhandled fetch: ${url}`);
  };

  win.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : input?.url || '';
    return resolver(url, init);
  };
}

describe('Cross-page accreditation flows', () => {
  it('dashboard reuses snapshot metrics for cards', () => {
    serveStaticPage('dashboard.html', {
      onBeforeLoad(win) {
        installApiStub(win);
        win.history.replaceState({}, '', 'https://platform.mapmystandards.ai/dashboard.html');
      },
    });

    cy.get('#documentsCard .metric-value', { timeout: 8000 }).should('contain', '5');
    cy.window().then((win) => {
      const snapshot = win.A3EMetricsStore.snapshot();
      expect(snapshot.coreMetrics.documents_analyzed).to.equal(5);
      expect(win.__fetchHits.metrics).to.equal(1);
    });
  });

  it('analysis results gate report generation until mappings exist', () => {
    const analysisWithMappings = {
      analysis: {
        mapped_standards: [
          {
            standard_code: 'HLC.1.A',
            confidence: 0.82,
            excerpts: ['Example excerpt'],
            standard: {
              code: 'HLC.1.A',
              title: 'Mission and Integrity',
              description: 'Demonstrate mission compliance.',
            },
          },
        ],
        mapped_count: 1,
        accreditor: 'HLC',
        accreditor_name: 'HLC',
        accreditor_display: 'Higher Learning Commission',
        accreditor_metrics: {
          total_mapped: 1,
        },
      },
      document: {
        filename: 'policy.pdf',
        analyzed_at: new Date().toISOString(),
      },
    };

    serveStaticPage('analysis-results.html', {
      query: '?document=test-doc',
      onBeforeLoad(win) {
        installApiStub(win);
        win.fetch = (input) => {
          const url = typeof input === 'string' ? input : input?.url || '';
          if (url.includes('/analysis')) {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => analysisWithMappings,
            });
          }
          if (url.includes('/crosswalk')) {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => apiPayloads.crosswalk,
            });
          }
          throw new Error(`Unhandled analysis fetch: ${url}`);
        };
        win.history.replaceState({}, '', 'https://platform.mapmystandards.ai/analysis-results.html?document=test-doc');
        win.localStorage.setItem('access_token', 'test-token');
      },
    });

    cy.get('#generateReportBtn').should('not.have.attr', 'disabled');
    cy.get('#generateReportStatus').should('have.css', 'display', 'none');
  });

  it('analysis results shows prerequisite message when no mappings available', () => {
    const analysisWithoutMappings = {
      analysis: {
        mapped_standards: [],
        mapped_count: 0,
        accreditor: 'HLC',
        accreditor_name: 'HLC',
        accreditor_display: 'Higher Learning Commission',
        accreditor_metrics: {
          total_mapped: 0,
        },
        accreditor_summary: [],
        accreditor_codes: [],
      },
      document: {
        filename: 'policy.pdf',
        analyzed_at: new Date().toISOString(),
      },
    };

    serveStaticPage('analysis-results.html', {
      query: '?document=empty-doc',
      onBeforeLoad(win) {
        installApiStub(win);
        win.fetch = (input) => {
          const url = typeof input === 'string' ? input : input?.url || '';
          if (url.includes('/analysis')) {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => analysisWithoutMappings,
            });
          }
          if (url.includes('/crosswalk')) {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => apiPayloads.crosswalk,
            });
          }
          throw new Error(`Unhandled analysis fetch: ${url}`);
        };
        win.history.replaceState({}, '', 'https://platform.mapmystandards.ai/analysis-results.html?document=empty-doc');
        win.localStorage.setItem('access_token', 'test-token');
      },
    });

    cy.get('#generateReportBtn').should('have.attr', 'disabled');
    cy.get('#generateReportStatus')
      .invoke('text')
      .should('contain', 'Map at least one evidence snippet');
  });

  it('report generation unlocks export actions when snapshot is complete', () => {
    serveStaticPage('report-generation.html', {
      onBeforeLoad(win) {
        installApiStub(win);
        win.history.replaceState({}, '', 'https://platform.mapmystandards.ai/report-generation.html');
      },
    });

    cy.get('#downloadReportBtn', { timeout: 10000 }).should('not.have.attr', 'disabled');
    cy.get('#reportStatusMessage').invoke('text').should('contain', 'Report ready');

    cy.window().then((win) => {
      expect(win.__fetchHits.metrics).to.equal(1);
      expect(win.__fetchHits.evidenceMap).to.equal(1);
      expect(win.__fetchHits.gaps).to.equal(1);
    });
  });

  it('gap analysis uses shared snapshot stats when evidence is available', () => {
    serveStaticPage('gap-analysis.html', {
      onBeforeLoad(win) {
        installApiStub(win);
        win.history.replaceState({}, '', 'https://platform.mapmystandards.ai/gap-analysis.html');
      },
    });

    cy.get('#mainContent', { timeout: 8000 }).should('be.visible');
    cy.contains('.metric-label', 'Critical Gaps')
      .parent()
      .find('.metric-value')
      .should('contain', '1');
    cy.window().then((win) => {
      const snapshot = win.A3EMetricsStore.snapshot();
      expect(snapshot.evidenceStats.mappedCount).to.equal(7);
      expect(win.__fetchHits.gaps).to.equal(1);
    });
  });
});
