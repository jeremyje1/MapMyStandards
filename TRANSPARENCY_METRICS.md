# Transparency & Metrics Reference

This document explains how core accreditation assistant metrics are derived, the meaning of each risk / trust dimension, and the schema for corpus metadata.

## Overview
The platform surfaces three major classes of transparency signals:
1. Coverage & Compliance Progress
2. Evidence Trust (quality of mapped evidence)
3. Gap Risk (likelihood a standard remains insufficiently evidenced)
4. Corpus Metadata Provenance (versioning & licensing context)

All API endpoints expose explanatory strings alongside numeric values to allow UI tooltips and user education.

---
## 1. Coverage & Compliance

### 1.1 Coverage
Coverage represents the proportion of standards for which at least one evidence mapping exists for the current user.

Formula (runtime user metrics):
```
coverage = mapped_unique_standards / total_loaded_standards_for_selected_accreditor
coverage_percentage = round(coverage * 100, 1)
```
Fallback: If the system lacks a per-user scope (e.g., before any uploads), coverage may reflect cached global scaffolding or return 0.

### 1.2 Compliance Score
The compliance score (shown in the dashboard) blends raw coverage with average evidence trust to reflect *quality-adjusted* progress.
```
compliance_score = (coverage * 0.6) + (avg_trust * 0.4)
```
- Weighting rationale: Reliable evidence quality can partially compensate for incomplete breadth, but breadth is prioritized (60%).
- Value range: 0–1 (UI often scales to percentage).

---
## 2. Evidence Trust
Evidence Trust estimates the reliability of mapped evidence for a standard.

### 2.1 Per-Standard Evidence Trust
Each mapping contributes a trust score (0–1) derived from internal heuristic / model signals (e.g., source type, recency, text match quality). The average for all mapped evidence tied to a single standard produces that standard's trust.
```
standard_trust = mean(evidence_item.trust_score for evidence_item in standard_mappings)
```
If no evidence exists for a standard, it is excluded from the average_trust aggregation (avoids penalizing unmapped standards twice—risk handles that).

### 2.2 Aggregate Evidence Trust
```
average_trust = mean(standard_trust for standards_with_any_evidence)
```
Fallback: If no standards contain evidence yet, average_trust defaults to 0.0 and explanation clarifies the absence of data.

Interpretation bands (suggested for UI coloring):
- 0.80–1.00: High Confidence
- 0.55–0.79: Moderate Confidence
- 0.30–0.54: Low Confidence
- < 0.30: Very Low / Unverified

---
## 3. Gap Risk
Gap Risk expresses the relative likelihood that a standard, if evaluated now, would be judged insufficient due to missing or weak evidence.

### 3.1 Factor Model
Each standard's risk is a weighted combination of calibrated component factors (0–1). Final values are clipped to [0,1]. Example current factors:
```
final_risk = (0.40 * coverage_gap_component)
           + (0.25 * evidence_quality_component)
           + (0.20 * mapping_density_component)
           + (0.15 * recency_component)
```
Where:
- coverage_gap_component = 1 - (coverage_percentage / 100)
- evidence_quality_component = 1 - standard_trust (or 1 if no trust data)
- mapping_density_component penalizes sparse mapping counts (non-linear scaling; saturates with adequate volume)
- recency_component increases risk if all evidence is old / stale

NOTE: Exact internal weighting/factors can evolve; the endpoint always emits a per-standard breakdown for transparency when scoring endpoints are used.

### 3.2 Distribution Buckets
Aggregated risk distribution in `/dashboard/metrics` reports counts across categorical buckets:
```
critical: risk >= 0.85
high:     0.70–0.84
medium:   0.40–0.69
low:      0.15–0.39
minimal:  < 0.15
```
These thresholds emphasize quick identification of areas requiring urgent remediation.

### 3.3 Average Risk
```
average_risk = mean(risk_score for scored_standards)
```
Unscored standards (e.g., missing structural data) are skipped. If no standards are scored yet, average_risk defaults to 0.0 with explanatory context.

---
## 4. Corpus Metadata Schema
Served by: `GET /api/user/intelligence-simple/standards/corpus/metadata`

Response Envelope:
```
{
  "success": true,
  "generated_at": ISO8601,
  "total_accreditors": int,
  "total_standards": int,
  "accreditors": [ MetadataRecord, ... ]
}
```
MetadataRecord Fields:
| Field | Description |
|-------|-------------|
| accreditor | Accreditor code / identifier (uppercase). |
| name | Human-readable accreditor name (if provided). |
| version | Corpus or standards release version captured from file metadata. |
| effective_date | Date the version became effective (if present). |
| last_updated | Last known revision timestamp (source). |
| source_url | Original public source or reference URL (if available). |
| license | Licensing terms or classification for the text. |
| disclaimer | Any disclaimer text provided in the corpus file. |
| coverage_notes | Notes about partial or placeholder coverage (e.g., synthetic placeholders). |
| standard_count | Declared number of standards present in the file. |
| loaded_node_count | Number of standard nodes actually ingested into the active graph. |
| file | Source filename loaded. |

### 4.1 Provenance & Integrity
- The loader caches metadata in-memory during `load_corpus()`; it does not auto-refresh mid-process.
- If corpus files change, an explicit reload is required (service restart or invoking the loader directly) before metadata reflects changes.

---
## 5. Endpoint Summary
| Purpose | Endpoint | Notes |
|---------|----------|-------|
| Dashboard metrics (coverage, trust, risk distribution) | `/api/user/intelligence-simple/dashboard/metrics` | Primary consolidated transparency payload. |
| Per-standard risk score | `/api/user/intelligence-simple/risk/score-standard` | Accepts standard_id; returns factor breakdown. |
| Bulk risk scoring | `/api/user/intelligence-simple/risk/score-bulk` | Scores multiple standards at once. |
| Risk aggregation | `/api/user/intelligence-simple/risk/aggregate` | Converts bulk scores into distribution + stats. |
| Corpus metadata | `/api/user/intelligence-simple/standards/corpus/metadata` | Provides provenance & versioning details. |

---
## 6. Interpretation Guidance
- Rising coverage with flat high risk implies weak/low-quality evidence—focus on improving trust sources.
- Declining average risk while coverage rises signals healthy maturation of the evidence base.
- A large "critical" bucket indicates structural mapping gaps—target immediate remediation.
- Use corpus metadata (version/effective_date) to align internal planning cycles with accreditor release cadence.

---
## 7. Future Enhancements (Planned)
- Factor-level UI modal surfacing raw component values per standard.
- Time-series snapshots (change in coverage, trust, risk week-over-week).
- Provenance hash / integrity attestations for loaded corpus files.
- Exportable JSON transparency report for audit handoffs.

---
## 8. Change Log
| Date | Change |
|------|--------|
| 2025-09-15 | Initial transparency & metrics reference drafted. |

---
For questions or clarifications, contact the platform team or consult inline API `explanations` fields.
