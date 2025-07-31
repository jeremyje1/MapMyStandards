"""
Core domain logic and business rules for A³E
Proprietary accreditation intelligence platform
"""

from .standards_config import StandardsConfigLoader
from .accreditation_ontology import AccreditationOntology, AccreditationDomain, EvidenceType, accreditation_ontology
from .vector_matching import VectorWeightedMatcher, MatchingStrategy, StandardMatch, EvidenceDocument
from .multi_agent_pipeline import MultiAgentPipeline, AgentRole, PipelineContext, ProcessingPhase
from .audit_trail import AuditTrailSystem, AuditEvent, TraceabilityLink, initialize_audit_system, get_audit_system

__all__ = [
    "StandardsConfigLoader",
    "AccreditationOntology", 
    "AccreditationDomain",
    "EvidenceType",
    "accreditation_ontology",
    "VectorWeightedMatcher",
    "MatchingStrategy", 
    "StandardMatch",
    "EvidenceDocument",
    "MultiAgentPipeline",
    "AgentRole",
    "PipelineContext", 
    "ProcessingPhase",
    "AuditTrailSystem",
    "AuditEvent",
    "TraceabilityLink",
    "initialize_audit_system",
    "get_audit_system"
]
