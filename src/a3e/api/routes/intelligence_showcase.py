"""Stub endpoints for proprietary intelligence experiences."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from ...core.config import settings

router = APIRouter(tags=["Intelligence Showcase"])


def _require_feature(flag: str) -> None:
    if not settings.is_feature_enabled(flag):
        raise HTTPException(status_code=404, detail=f"Feature '{flag}' is disabled")


@router.get("/feature-flags", response_model=Dict[str, bool])
def get_feature_flags() -> Dict[str, bool]:
    """Expose current feature-flag state for frontend gating."""
    return dict(settings.feature_flags)


@router.get("/intelligence/standards-graph")
def standards_graph_stub() -> Dict[str, Any]:
    _require_feature("standards_graph")
    return {
        "graph": {
            "nodes": [
                {"id": "inst_001", "label": "Institution", "type": "institution"},
                {"id": "std_101", "label": "Standard 101", "type": "standard"},
                {"id": "evi_a", "label": "Evidence A", "type": "evidence"},
            ],
            "edges": [
                {"source": "inst_001", "target": "std_101", "relationship": "obligation"},
                {"source": "evi_a", "target": "std_101", "relationship": "supports"},
            ],
        },
        "metadata": {
            "generated_at": settings.environment.value,
            "confidence": 0.82,
            "next_refresh_seconds": 300,
        },
    }


@router.get("/intelligence/evidence-mapper")
def evidence_mapper_stub() -> Dict[str, Any]:
    _require_feature("evidence_mapper")
    return {
        "mappings": [
            {
                "evidence_id": "evi_a",
                "standard_id": "std_101",
                "alignment": "strong",
                "notes": "Policy references the required clause explicitly.",
            },
            {
                "evidence_id": "evi_b",
                "standard_id": "std_102",
                "alignment": "partial",
                "notes": "Training logs cover 75% of competency outcomes.",
            },
        ],
        "summary": {
            "coverage_percent": 68,
            "gaps": 3,
            "recommended_actions": ["Collect updated assessment reports", "Add board minutes"],
        },
    }


@router.get("/intelligence/evidence-trust")
def evidence_trust_stub() -> Dict[str, Any]:
    _require_feature("evidence_trust_score")
    return {
        "documents": [
            {"id": "evi_a", "title": "Academic Integrity Policy", "trust_score": 0.91},
            {"id": "evi_b", "title": "Faculty Training Logs", "trust_score": 0.73},
            {"id": "evi_c", "title": "Course Assessment Summary", "trust_score": 0.58},
        ],
        "methodology": {
            "signals": ["authorship", "freshness", "citation_density", "chain_of_custody"],
            "ensemble_version": "0.1-stub",
        },
    }


@router.get("/intelligence/gap-risk")
def gap_risk_stub() -> Dict[str, Any]:
    _require_feature("gap_risk_predictor")
    return {
        "risk_profile": {
            "overall_risk": "moderate",
            "risk_score": 0.64,
            "drivers": [
                {"factor": "Assessment Data Freshness", "impact": "high"},
                {"factor": "Faculty Qualifications", "impact": "medium"},
            ],
        },
        "timeline": [
            {"milestone": "Next accreditation visit", "date": "2026-03-01", "risk": "high"},
            {"milestone": "Mid-cycle review", "date": "2024-11-15", "risk": "medium"},
        ],
    }


@router.get("/intelligence/crosswalkx")
def crosswalk_stub() -> Dict[str, Any]:
    _require_feature("crosswalkx")
    return {
        "source_framework": "Middle States 2022",
        "target_framework": "HLC 2020",
        "matches": [
            {
                "source": "MSCHE 1.1",
                "target": "HLC 1.A",
                "confidence": 0.9,
                "notes": "Governance expectations align closely.",
            },
            {
                "source": "MSCHE 3.2",
                "target": "HLC 3.B",
                "confidence": 0.78,
                "notes": "Curriculum oversight similar with minor terminology shifts.",
            },
        ],
        "unmatched_source": ["MSCHE 4.4"],
        "unmatched_target": ["HLC 5.C"],
    }


@router.get("/intelligence/citeguard")
def citeguard_stub() -> Dict[str, Any]:
    _require_feature("citeguard")
    return {
        "document_id": "evi_a",
        "issues": [
            {
                "citation": "Standard 3.2",
                "status": "missing",
                "recommendation": "Reference the 2024 program review minutes.",
            },
            {
                "citation": "Policy Section 5.1",
                "status": "outdated",
                "recommendation": "Update to match 2023 revision.",
            },
        ],
        "summary": {
            "flagged": 2,
            "auto_resolvable": 1,
            "needs_review": 1,
        },
    }


__all__: List[str] = ["router"]
