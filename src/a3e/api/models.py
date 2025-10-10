"""Pydantic models for AI endpoints (EvidenceMapper, StandardsGraph, etc.)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class EvidenceMapRequest(BaseModel):
    artifact_id: str
    standard_set: str
    top_k: int = Field(default=5, ge=1, le=50)
    threshold: float = Field(default=0.62, ge=0.0, le=1.0)
    explain: bool = True


class EvidenceSpan(BaseModel):
    page: int
    start: Optional[int] = None
    end: Optional[int] = None


class EvidenceMatch(BaseModel):
    standard_id: str
    score: float
    evidence_spans: List[EvidenceSpan] = []
    rationale: Optional[str] = None
    evidence_trust: Optional[float] = None
    citations: Optional[list] = None


class EvidenceMapResponse(BaseModel):
    artifact_id: str
    matches: List[EvidenceMatch]
    computed_at: datetime


class IngestStandardsRequest(BaseModel):
    standard_set: str
    source_url: Optional[str] = None
    parse_mode: Optional[Literal["html", "pdf", "markdown"]] = "html"


class StandardsGraphNode(BaseModel):
    id: str
    type: Literal["clause"]
    title: Optional[str] = None


class StandardsGraphEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: str

    class Config:
        populate_by_name = True


class StandardsGraphResponse(BaseModel):
    nodes: List[StandardsGraphNode]
    edges: List[StandardsGraphEdge]


class CrosswalkBuildRequest(BaseModel):
    from_set: str
    to_set: str
    method: Optional[Literal["batch", "refine"]] = "batch"


class CrosswalkPair(BaseModel):
    from_: str = Field(alias="from")
    to: str
    confidence: float
    rationale: Optional[str] = None

    class Config:
        populate_by_name = True


class CrosswalkResponse(BaseModel):
    pairs: List[CrosswalkPair]


class RiskCoverageResponse(BaseModel):
    coverage: float
    gaps: list
    risk_index: float
    recommendations: list


class TrustScoreRequest(BaseModel):
    artifact_id: str


class TrustScoreSignals(BaseModel):
    freshness: float
    authenticity: float
    redundancy: float
    citation_density: float


class TrustScoreResponse(BaseModel):
    artifact_id: str
    trust: float
    signals: TrustScoreSignals
    explanation: str


class CiteValidateRequest(BaseModel):
    artifact_id: str
    style: Literal["APA7", "Chicago", "Internal"] = "Internal"


class CiteValidateResponse(BaseModel):
    artifact_id: str
    status: Literal["pass", "warn", "fail"]
    issues: list
