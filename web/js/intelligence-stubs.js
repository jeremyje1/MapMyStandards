'use strict';

const FEATURE_ENDPOINTS = {
  standards_graph: {
    endpoint: '/api/v1/intelligence/standards-graph',
    container: '#standardsGraphContainer',
    render: (data) => {
      const container = document.querySelector('#standardsGraphData');
      if (!container) return;
      container.innerHTML = data.graph.nodes
        .map((node) => `<li><strong>${node.label}</strong> <span class="badge">${node.type}</span></li>`)
        .join('');
    },
  },
  evidence_mapper: {
    endpoint: '/api/v1/intelligence/evidence-mapper',
    container: '#evidenceMapperContainer',
    render: (data) => {
      const container = document.querySelector('#evidenceMapperData');
      if (!container) return;
      container.innerHTML = data.mappings
        .map((mapping) => `<li><strong>${mapping.evidence_id}</strong> → ${mapping.standard_id} <em>${mapping.alignment}</em></li>`)
        .join('');
    },
  },
  evidence_trust_score: {
    endpoint: '/api/v1/intelligence/evidence-trust',
    container: '#evidenceTrustContainer',
    render: (data) => {
      const container = document.querySelector('#evidenceTrustData');
      if (!container) return;
      container.innerHTML = data.documents
        .map((doc) => `<li>${doc.title} – <strong>${Math.round(doc.trust_score * 100)}%</strong></li>`)
        .join('');
    },
  },
  gap_risk_predictor: {
    endpoint: '/api/v1/intelligence/gap-risk',
    container: '#gapRiskContainer',
    render: (data) => {
      const container = document.querySelector('#gapRiskData');
      if (!container) return;
      container.innerHTML = `
        <p class="metric">Overall risk: <strong>${data.risk_profile.overall_risk}</strong></p>
        <ul>
          ${data.risk_profile.drivers
            .map((driver) => `<li>${driver.factor} – <em>${driver.impact}</em></li>`)
            .join('')}
        </ul>
      `;
    },
  },
  crosswalkx: {
    endpoint: '/api/v1/intelligence/crosswalkx',
    container: '#crosswalkContainer',
    render: (data) => {
      const container = document.querySelector('#crosswalkData');
      if (!container) return;
      container.innerHTML = data.matches
        .map(
          (match) => `<li><strong>${match.source}</strong> ↔ ${match.target} <span>${Math.round(
            match.confidence * 100
          )}%</span></li>`
        )
        .join('');
    },
  },
  citeguard: {
    endpoint: '/api/v1/intelligence/citeguard',
    container: '#citeguardContainer',
    render: (data) => {
      const container = document.querySelector('#citeguardData');
      if (!container) return;
      container.innerHTML = data.issues
        .map((issue) => `<li>${issue.citation} – ${issue.status} <em>${issue.recommendation}</em></li>`)
        .join('');
    },
  },
};

async function bootstrapIntelligenceShowcase() {
  const status = document.querySelector('#featureFlagStatus');
  try {
    const response = await fetch('/api/v1/feature-flags');
    if (!response.ok) throw new Error(`Feature flag request failed: ${response.status}`);
    const flags = await response.json();

    Object.entries(FEATURE_ENDPOINTS).forEach(([flag, config]) => {
      const section = document.querySelector(config.container);
      if (!section) return;
      if (!flags[flag]) {
        section.classList.add('is-disabled');
        section.querySelector('.feature-body').innerHTML =
          '<p class="text-muted">Disabled in current environment.</p>';
        return;
      }

      fetch(config.endpoint)
        .then((res) => {
          if (!res.ok) throw new Error(`Endpoint ${config.endpoint} returned ${res.status}`);
          return res.json();
        })
        .then((data) => {
          config.render(data);
          section.classList.add('is-loaded');
        })
        .catch((err) => {
          section.querySelector('.feature-body').innerHTML = `<p class="error">${err.message}</p>`;
        });
    });

    if (status) status.textContent = 'Live feature flags pulled from API';
  } catch (error) {
    if (status) status.textContent = `Unable to load feature flags: ${error.message}`;
  }
}

document.addEventListener('DOMContentLoaded', bootstrapIntelligenceShowcase);
