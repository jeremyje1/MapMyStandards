"""Risk Transparency Layer

Provides aggregated and per-standard gap risk breakdowns using existing
`gap_risk_predictor` plus lightweight derivations from evidence mapping data.

Design Goals:
- No heavy database dependency: accept injected / cached lightweight structures
- Deterministic, explainable outputs with factor weights & raw inputs
- Aggregations for dashboard: distribution buckets, avg trust, top factors
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from statistics import mean
import logging
from .gap_risk_predictor import gap_risk_predictor, GapRiskScore

logger = logging.getLogger(__name__)


@dataclass
class StandardEvidenceSnapshot:
    standard_id: str
    coverage_percent: float
    trust_scores: List[float]
    evidence_ages_days: List[int]
    overdue_tasks: int = 0
    total_tasks: int = 0
    recent_changes: int = 0
    historical_findings: int = 0
    days_to_review: int = 180

    def to_inputs(self) -> Dict[str, Any]:
        return dict(
            standard_id=self.standard_id,
            coverage_percentage=self.coverage_percent,
            evidence_trust_scores=self.trust_scores,
            evidence_ages_days=self.evidence_ages_days,
            overdue_tasks_count=self.overdue_tasks,
            total_tasks_count=self.total_tasks,
            recent_changes_count=self.recent_changes,
            historical_findings_count=self.historical_findings,
            time_to_next_review_days=self.days_to_review,
        )


class RiskExplainer:
    def __init__(self):
        self._last_scores: Dict[str, GapRiskScore] = {}

    def compute_standard_risk(self, snapshot: StandardEvidenceSnapshot) -> GapRiskScore:
        score = gap_risk_predictor.predict_risk(**snapshot.to_inputs())
        self._last_scores[score.standard_id] = score
        return score

    def compute_bulk(self, snapshots: List[StandardEvidenceSnapshot]) -> List[GapRiskScore]:
        return [self.compute_standard_risk(s) for s in snapshots]

    def aggregate(self) -> Dict[str, Any]:
        if not self._last_scores:
            return {
                "standards_scored": 0,
                "average_risk": 0.0,
                "risk_distribution": {},
                "average_trust": 0.0,
                "top_risk_factors": [],
            }
        scores = list(self._last_scores.values())
        risk_values = [s.risk_score for s in scores]
        avg_risk = sum(risk_values)/len(risk_values)
        # Distribution by level
        dist: Dict[str, int] = {}
        factor_contrib: Dict[str, float] = {}
        trust_vals: List[float] = []
        for s in scores:
            dist[s.risk_level.value] = dist.get(s.risk_level.value, 0) + 1
            for f in s.factors:
                factor_contrib[f.factor_name] = factor_contrib.get(f.factor_name, 0.0) + f.contribution
                if f.factor_name == 'trust':
                    trust_vals.append(1.0 - f.normalized_value)  # original avg trust value
        # Normalize factor contributions
        total_contrib = sum(factor_contrib.values()) or 1.0
        top_factors = sorted(
            [
                {
                    "factor": k,
                    "aggregate_contribution": round(v, 4),
                    "percent_of_total": round((v/total_contrib)*100, 2),
                }
                for k, v in factor_contrib.items()
            ], key=lambda x: x["aggregate_contribution"], reverse=True
        )[:5]
        return {
            "standards_scored": len(scores),
            "average_risk": round(avg_risk, 4),
            "risk_distribution": dist,
            "average_trust": round(mean(trust_vals), 4) if trust_vals else 0.0,
            "top_risk_factors": top_factors,
        }

    def explain_standard(self, standard_id: str) -> Dict[str, Any]:
        score = self._last_scores.get(standard_id)
        if not score:
            return {"standard_id": standard_id, "status": "not_scored"}
        return {
            "standard_id": standard_id,
            "risk_score": score.risk_score,
            "risk_level": score.risk_level.value,
            "confidence": score.confidence,
            "predicted_issues": score.predicted_issues,
            "remediation_priority": score.remediation_priority,
            "factors": [f.to_dict() for f in score.factors],
        }

risk_explainer = RiskExplainer()
