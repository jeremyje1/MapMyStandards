"""
Enhanced API routes showcasing proprietary A³E capabilities
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ...services.proprietary_a3e_service import ProprietaryA3EService
from ...core import AccreditationDomain, EvidenceType, MatchingStrategy, TraceabilityLevel
from ...dependencies import get_proprietary_a3e_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/proprietary", tags=["Proprietary A³E"])

# Request/Response Models

class EvidenceDocumentRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    evidence_type: str = Field(..., description="Type of evidence document")
    source_system: Optional[str] = Field("api_input", description="Source system identifier")

class AccreditationAnalysisRequest(BaseModel):
    institution_id: str = Field(..., description="Institution identifier")
    accreditor_id: str = Field(..., description="Accrediting body identifier")
    evidence_documents: List[EvidenceDocumentRequest] = Field(..., description="Evidence documents to analyze")
    standards_scope: List[str] = Field(..., description="Standards to evaluate against")
    user_id: Optional[str] = Field(None, description="User identifier for audit trail")
    traceability_level: Optional[str] = Field("standard", description="Level of audit traceability")

class SingleEvidenceAnalysisRequest(BaseModel):
    evidence_title: str = Field(..., description="Evidence document title")
    evidence_content: str = Field(..., description="Evidence document content")
    evidence_type: str = Field(..., description="Type of evidence")
    standards_to_check: List[str] = Field(..., description="Standards to check against")

class OntologyQueryRequest(BaseModel):
    concept_id: Optional[str] = Field(None, description="Specific concept to query")
    domain: Optional[str] = Field(None, description="Domain to explore")
    search_term: Optional[str] = Field(None, description="Search term for concepts")

class TraceabilityRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to trace")
    output_id: Optional[str] = Field(None, description="Specific output to trace")

# API Endpoints

@router.post("/analyze/complete")
async def complete_accreditation_analysis(
    request: AccreditationAnalysisRequest,
    background_tasks: BackgroundTasks,
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Complete accreditation analysis using proprietary four-agent pipeline.
    
    Features:
    - Proprietary accreditation ontology + embeddings schema
    - Vector-weighted standards-matching algorithm
    - Multi-agent LLM pipeline (Mapper → GapFinder → Narrator → Verifier)
    - Audit-ready traceability system
    """
    
    try:
        # Convert request to internal format
        evidence_docs = []
        for doc in request.evidence_documents:
            evidence_docs.append({
                "id": None,  # Will be auto-generated
                "title": doc.title,
                "content": doc.content,
                "evidence_type": doc.evidence_type,
                "source_system": doc.source_system
            })
        
        # Execute complete analysis
        results = await a3e_service.process_accreditation_analysis(
            institution_id=request.institution_id,
            accreditor_id=request.accreditor_id,
            evidence_documents=evidence_docs,
            standards_scope=request.standards_scope,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "message": "Complete accreditation analysis executed successfully",
            "data": results,
            "proprietary_features": {
                "ontology_enabled": True,
                "vector_matching_enabled": True,
                "multi_agent_pipeline_enabled": True,
                "audit_traceability_enabled": True
            }
        }
        
    except Exception as e:
        logger.error(f"Complete analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/evidence")
async def analyze_single_evidence(
    request: SingleEvidenceAnalysisRequest,
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Analyze a single piece of evidence using proprietary vector-weighted matching.
    
    Demonstrates:
    - Proprietary embedding schema
    - Vector-weighted similarity scoring
    - Ontology concept mapping
    - Multi-dimensional analysis
    """
    
    try:
        results = await a3e_service.analyze_single_evidence(
            evidence_content=request.evidence_content,
            evidence_title=request.evidence_title,
            evidence_type=request.evidence_type,
            standards_to_check=request.standards_to_check
        )
        
        return {
            "success": True,
            "message": "Single evidence analysis completed",
            "data": results,
            "analysis_features": {
                "proprietary_embeddings": True,
                "vector_weighted_matching": True,
                "ontology_mapping": True,
                "quality_scoring": True
            }
        }
        
    except Exception as e:
        logger.error(f"Single evidence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evidence analysis failed: {str(e)}")

@router.get("/ontology/insights")
async def get_ontology_insights(
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Get insights about the proprietary accreditation ontology.
    
    Returns:
    - Ontology structure and statistics
    - Domain distribution
    - Concept hierarchies
    - Embedding schema information
    """
    
    try:
        insights = await a3e_service.get_ontology_insights()
        
        return {
            "success": True,
            "message": "Ontology insights retrieved successfully",
            "data": insights,
            "proprietary_features": {
                "hierarchical_concepts": True,
                "domain_specific_embeddings": True,
                "semantic_relationships": True,
                "accreditor_mappings": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get ontology insights: {e}")
        raise HTTPException(status_code=500, detail=f"Ontology insights failed: {str(e)}")

@router.post("/ontology/query")
async def query_ontology(
    request: OntologyQueryRequest,
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Query the proprietary accreditation ontology.
    
    Supports:
    - Concept lookup by ID
    - Domain exploration
    - Semantic search
    - Relationship traversal
    """
    
    try:
        ontology = a3e_service.ontology
        results = {}
        
        if request.concept_id:
            # Get specific concept
            if request.concept_id in ontology.nodes:
                concept = ontology.nodes[request.concept_id]
                results["concept"] = {
                    "id": concept.id,
                    "label": concept.label,
                    "domain": concept.domain.value,
                    "synonyms": concept.synonyms,
                    "related_concepts": concept.related_concepts,
                    "children": concept.children_ids,
                    "parent": concept.parent_id,
                    "evidence_requirements": ontology.get_evidence_requirements(concept.id)
                }
                
                # Get hierarchy
                results["hierarchy"] = ontology.get_concept_hierarchy(request.concept_id)
                
                # Get related concepts
                results["related"] = ontology.find_related_concepts(request.concept_id, max_distance=2)
        
        if request.domain:
            # Get domain concepts
            try:
                domain_enum = AccreditationDomain(request.domain)
                domain_concepts = ontology.get_domain_concepts(domain_enum)
                results["domain_concepts"] = [
                    {
                        "id": concept.id,
                        "label": concept.label,
                        "synonyms": concept.synonyms
                    }
                    for concept in domain_concepts
                ]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid domain: {request.domain}")
        
        if request.search_term:
            # Search concepts
            search_results = []
            search_lower = request.search_term.lower()
            
            for concept in ontology.nodes.values():
                if (search_lower in concept.label.lower() or
                    any(search_lower in synonym.lower() for synonym in concept.synonyms)):
                    search_results.append({
                        "id": concept.id,
                        "label": concept.label,
                        "domain": concept.domain.value,
                        "relevance_score": 1.0  # Could implement actual scoring
                    })
            
            results["search_results"] = search_results[:20]  # Limit results
        
        return {
            "success": True,
            "message": "Ontology query completed",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Ontology query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ontology query failed: {str(e)}")

@router.get("/traceability/{session_id}")
async def get_traceability_report(
    session_id: str,
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Get complete audit traceability report for a session.
    
    Features:
    - Complete audit trail from evidence to output
    - LLM interaction logging
    - Agent processing traceability
    - Integrity verification
    """
    
    try:
        # Generate audit report
        audit_report = a3e_service.audit_system.generate_audit_report(session_id)
        
        return {
            "success": True,
            "message": "Traceability report generated successfully",
            "data": audit_report,
            "traceability_features": {
                "immutable_audit_trail": True,
                "llm_interaction_logging": True,
                "evidence_to_output_mapping": True,
                "integrity_verification": True
            }
        }
        
    except Exception as e:
        logger.error(f"Traceability report failed: {e}")
        raise HTTPException(status_code=500, detail=f"Traceability report failed: {str(e)}")

@router.post("/traceability/trace")
async def trace_output_to_sources(
    request: TraceabilityRequest,
    a3e_service: ProprietaryA3EService = Depends(get_proprietary_a3e_service)
) -> Dict[str, Any]:
    """
    Trace specific output back to all evidentiary sources.
    
    Provides:
    - Complete evidence chain
    - Confidence scoring
    - Verification status
    - Integrity validation
    """
    
    try:
        if not request.output_id:
            # Get session overview
            audit_report = a3e_service.audit_system.generate_audit_report(request.session_id)
            return {
                "success": True,
                "message": "Session overview retrieved",
                "data": audit_report
            }
        
        # Trace specific output
        trace_results = a3e_service.audit_system.trace_output_to_sources(request.output_id)
        
        return {
            "success": True,
            "message": "Output traceability completed",
            "data": trace_results,
            "traceability_validation": {
                "chain_integrity": trace_results.get("integrity_score", 0.0) >= 0.8,
                "verification_status": trace_results.get("verification_status", "unknown"),
                "total_links": trace_results.get("total_links", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Output tracing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Output tracing failed: {str(e)}")

@router.get("/capabilities")
async def get_proprietary_capabilities() -> Dict[str, Any]:
    """
    Get overview of all proprietary A³E capabilities.
    
    Returns complete feature set documentation.
    """
    
    return {
        "success": True,
        "message": "Proprietary A³E capabilities overview",
        "data": {
            "proprietary_features": {
                "accreditation_ontology": {
                    "description": "Hierarchical concept ontology with 500+ accreditation concepts",
                    "features": [
                        "Domain-specific concept hierarchies",
                        "Semantic relationship mapping",
                        "Accreditor-specific standard mappings",
                        "Evidence requirement specifications"
                    ],
                    "domains_supported": [domain.value for domain in AccreditationDomain],
                    "evidence_types": [etype.value for etype in EvidenceType]
                },
                "embeddings_schema": {
                    "description": "Multi-dimensional embedding schema optimized for accreditation",
                    "total_dimensions": 512,  # From ontology schema
                    "dimension_categories": [
                        "semantic_core", "mission", "academic", "student", "faculty",
                        "effectiveness", "financial", "infrastructure", "compliance",
                        "temporal", "complexity", "criticality", "context"
                    ],
                    "features": [
                        "Domain-specific embedding components",
                        "Temporal relevance encoding",
                        "Complexity level representation",
                        "Criticality weighting"
                    ]
                },
                "vector_matching_algorithm": {
                    "description": "Proprietary vector-weighted standards matching with multi-factor scoring",
                    "scoring_factors": [
                        "semantic_similarity (35%)",
                        "ontology_hierarchy (25%)", 
                        "domain_relevance (20%)",
                        "evidence_alignment (15%)",
                        "temporal_relevance (5%)"
                    ],
                    "matching_strategies": [strategy.value for strategy in MatchingStrategy],
                    "features": [
                        "Multi-dimensional similarity scoring",
                        "Hierarchical relationship weighting",
                        "Evidence type compatibility analysis",
                        "Temporal decay modeling"
                    ]
                },
                "multi_agent_pipeline": {
                    "description": "Four-agent LLM orchestration for comprehensive accreditation analysis",
                    "agents": [
                        {
                            "role": "Mapper",
                            "function": "Classifies artifacts to standards using vector matching + LLM validation"
                        },
                        {
                            "role": "GapFinder", 
                            "function": "Identifies missing evidence and gaps with severity scoring"
                        },
                        {
                            "role": "Narrator",
                            "function": "Drafts prose paragraphs and comprehensive narratives"
                        },
                        {
                            "role": "Verifier",
                            "function": "Validates citations with ≥0.85 cosine similarity requirement"
                        }
                    ],
                    "features": [
                        "Sequential and parallel processing modes",
                        "Agent output quality scoring",
                        "Error handling and recovery",
                        "Complete processing context preservation"
                    ]
                },
                "audit_traceability": {
                    "description": "Immutable audit trail system for complete LLM-to-evidence traceability",
                    "traceability_levels": [level.value for level in TraceabilityLevel],
                    "features": [
                        "Immutable event logging with integrity hashing",
                        "Complete LLM interaction capture",
                        "Evidence-to-output link mapping",
                        "Chain integrity validation",
                        "Forensic-level detail options"
                    ],
                    "audit_event_types": [
                        "Pipeline execution", "Agent processing", "LLM interactions",
                        "Evidence mapping", "Gap identification", "Narrative generation",
                        "Citation verification", "Report generation"
                    ]
                }
            },
            "competitive_advantages": [
                "Only system with hierarchical accreditation ontology",
                "Multi-dimensional embedding schema optimized for higher education",
                "Proprietary vector-weighted matching algorithm",
                "Four-agent LLM pipeline with role specialization",
                "Complete audit traceability from evidence to final output",
                "Support for all major US accrediting bodies",
                "Institution-type contextualization",
                "Real-time gap identification and severity scoring"
            ],
            "use_cases": [
                "Comprehensive accreditation self-study preparation",
                "Evidence gap identification and remediation",
                "Standards compliance verification",
                "Narrative generation for accreditation reports", 
                "Citation verification and validation",
                "Multi-accreditor support and comparison",
                "Institutional effectiveness assessment",
                "Audit trail generation for regulatory review"
            ]
        }
    }
