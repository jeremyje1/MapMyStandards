# Metrics Transparency

This document explains how key dashboard metrics are computed and bounded.

- Compliance Score: `(coverage * 0.7 + avg_trust * 0.3) * 100`, then clamped to `[0, 100]` and rounded to 1 decimal.
  - coverage: unique standards with any mapped evidence divided by total standards for the selected accreditor. Bounded `[0,1]`.
  - avg_trust: average of EvidenceTrust overall scores across uploaded documents. Interpreted in `[0,1]`. If values appear as percentages (e.g., 82), they are scaled down to `[0,1]`.
  - Default: If no trust scores are present, `avg_trust = 0.7`.

- Average Risk: Aggregated by GapRisk Predictor via `risk_explainer.aggregate()`, reported as a 0–1 score. UI can present as percentage if desired.

- Coverage Percentage: `coverage * 100`, rounded to 1 decimal.

Notes
- All intermediate values are normalized to avoid invalid outputs (e.g., > 100%).
- Future iterations may calibrate weights per accreditor or institution profile.
