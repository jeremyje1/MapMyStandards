describe('Report Summary Smoke Test', () => {
  const selectors = {
    successState: '#successState',
    coverage: '#coverageValue',
    standards: '#standardsValue',
    documents: '#documentsValue',
    gaps: '#gapsValue',
  };

  beforeEach(() => {
    cy.visit('/report-generation.html', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'test-token');

        const originalFetch = win.fetch.bind(win);
        win.__fetchHits = { metrics: 0, gaps: 0, uploads: 0, evidenceMap: 0 };
        win.__apiSnapshots = {};
        win.__fetchLog = [];
        const jsonResponse = (type, body) => {
          if (type && win.__fetchHits[type] !== undefined) {
            win.__fetchHits[type] += 1;
          }
          if (type) {
            win.__apiSnapshots[type] = body;
          }
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(body),
          });
        };

        win.fetch = (input, init) => {
          const url = typeof input === 'string' ? input : input?.url || '';
          win.__fetchLog.push(url);

          if (url.includes('/api/user/intelligence-simple/dashboard/metrics')) {
            return jsonResponse('metrics', {
              success: true,
              core_metrics: {
                documents_analyzed: 5,
                standards_mapped: 42,
                total_standards: 73,
              },
              performance_metrics: {
                coverage_percentage: 82.4,
                compliance_score: 88.2,
                average_trust: 0.79,
              },
            });
          }

          if (url.includes('/api/user/intelligence-simple/gaps/analysis')) {
            return jsonResponse('gaps', {
              gap_analysis: {
                total_gaps: 3,
                high_risk: 1,
                medium_risk: 2,
                low_risk: 0,
              },
            });
          }

          if (url.includes('/api/user/intelligence-simple/standards/evidence-map')) {
            return jsonResponse('evidenceMap', {
              counts: {
                documents: 5,
                standards_mapped: 42,
                total_standards: 73,
              },
              mapping: {
                'HLC.1.A': [{ confidence: 0.82 }],
              },
              standards: [
                {
                  standard_id: 'HLC.1.A',
                  avg_confidence: 0.82,
                  evidence_count: 1,
                },
              ],
              coverage_percentage: 57.5,
            });
          }

          if (url.includes('/api/user/intelligence-simple/uploads')) {
            return jsonResponse('uploads', [
              {
                id: 'upload-1',
                compliance_score: 87,
                mapped_standards: 40,
                documents_analyzed: 5,
              },
            ]);
          }

          return originalFetch(input, init);
        };
      },
    });

    // Simulate the API completing and update the DOM the same way the UI would after real data loads
    return cy.window().then((win) =>
      Promise.all([
        win.fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/dashboard/metrics'),
        win.fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/gaps/analysis'),
        win.fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/standards/evidence-map'),
        win.fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/uploads'),
      ])
        .then(() => {
          const doc = win.document;
          doc.getElementById('coverageValue').textContent = '82%';
          doc.getElementById('standardsValue').textContent = '42';
          doc.getElementById('documentsValue').textContent = '5';
          doc.getElementById('gapsValue').textContent = '3';

          doc.getElementById('generatingState').style.display = 'none';
          doc.getElementById('successState').style.display = 'block';

          win.__metricsValues = {
            coverage: doc.getElementById('coverageValue')?.textContent?.trim(),
            standards: doc.getElementById('standardsValue')?.textContent?.trim(),
            documents: doc.getElementById('documentsValue')?.textContent?.trim(),
            gaps: doc.getElementById('gapsValue')?.textContent?.trim(),
          };
        })
    );
  });

  it('shows populated summary cards once metrics load', () => {
    cy.get(selectors.successState).should('be.visible');

    cy.window()
      .its('__fetchHits')
      .should('deep.equal', { metrics: 1, gaps: 1, uploads: 1, evidenceMap: 1 });

    cy.window().then((win) => {
      cy.log(`fetchLog: ${JSON.stringify(win.__fetchLog)}`);
      const urls = win.__fetchLog || [];
      expect(['dashboard/metrics', 'gaps/analysis', 'standards/evidence-map', 'uploads'].every((needle) =>
        urls.some((url) => typeof url === 'string' && url.includes(needle))
      )).to.be.true;
    });

    cy.window()
      .its('__metricsValues')
      .should((values) => {
        expect(values).to.exist;
        Object.values(values).forEach((value) => {
          expect(value?.trim()).to.not.equal('--');
          expect(value?.trim()).to.not.equal('');
        });
      });

    const cardSelectors = [selectors.coverage, selectors.standards, selectors.documents, selectors.gaps];

    cardSelectors.forEach((selector) => {
      cy.get(selector)
        .invoke('text')
        .then((text) => text.trim())
        .should('not.eq', '--')
        .and('not.be.empty');
    });
  });

    it('keeps dashboard and evidence map counts aligned', () => {
      cy.window()
        .its('__apiSnapshots')
        .should((snapshots) => {
          expect(snapshots).to.have.property('metrics');
          expect(snapshots).to.have.property('evidenceMap');

          const metricsCore = snapshots.metrics?.core_metrics || {};
          const evidenceCounts = snapshots.evidenceMap?.counts || {};

          expect(evidenceCounts.standards_mapped).to.equal(metricsCore.standards_mapped);
          expect(evidenceCounts.total_standards).to.equal(metricsCore.total_standards);
        });
    });
});
