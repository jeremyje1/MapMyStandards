"""
Enhanced Multi-Agent LLM Pipeline for A³E
Proprietary four-agent orchestration: Mapper → GapFinder → Narrator → Verifier
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Optional numpy import
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Mock numpy for basic functionality
    class MockNdarray:
        def __init__(self, data):
            self.data = data
    
    class np:
        ndarray = MockNdarray  # For type hints
        
        @staticmethod
        def array(data):
            return MockNdarray(data)

from .accreditation_ontology import AccreditationOntology, AccreditationDomain, EvidenceType
from .vector_matching import VectorWeightedMatcher, StandardMatch, EvidenceDocument, MatchingStrategy
from .audit_trail import AuditTrailSystem, AuditEvent, TraceabilityLink

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Four-agent pipeline roles."""
    MAPPER = "mapper"           # Classifies artifacts → standards
    GAP_FINDER = "gap_finder"   # Identifies missing evidence
    NARRATOR = "narrator"       # Drafts prose paragraphs
    VERIFIER = "verifier"       # Validates citations (≥0.85 cosine)

class ProcessingPhase(Enum):
    """Processing phases in the pipeline."""
    INTAKE = "intake"
    MAPPING = "mapping"
    GAP_ANALYSIS = "gap_analysis"
    NARRATIVE_GENERATION = "narrative_generation"
    VERIFICATION = "verification"
    FINALIZATION = "finalization"

@dataclass
class AgentOutput:
    """Output from an individual agent."""
    agent_role: AgentRole
    phase: ProcessingPhase
    output_data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Quality metrics
    output_quality_score: float = 0.0
    error_flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Audit information
    input_artifacts: List[str] = field(default_factory=list)
    llm_model_used: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0

@dataclass
class PipelineContext:
    """Context object passed through the agent pipeline."""
    session_id: str
    institution_id: str
    accreditor_id: str
    standards_scope: List[str]
    
    # Evidence collection
    evidence_documents: List[EvidenceDocument] = field(default_factory=list)
    mapped_standards: Dict[str, List[StandardMatch]] = field(default_factory=dict)
    
    # Gap analysis results
    identified_gaps: List[Dict[str, Any]] = field(default_factory=list)
    gap_severity_scores: Dict[str, float] = field(default_factory=dict)
    
    # Narrative components
    section_narratives: Dict[str, str] = field(default_factory=dict)
    evidence_citations: Dict[str, List[str]] = field(default_factory=dict)
    
    # Verification results
    citation_verifications: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_verification_score: float = 0.0
    
    # Pipeline metadata
    start_time: datetime = field(default_factory=datetime.utcnow)
    agent_outputs: List[AgentOutput] = field(default_factory=list)
    current_phase: ProcessingPhase = ProcessingPhase.INTAKE

class BaseAgent:
    """Base class for all agents in the pipeline."""
    
    def __init__(self, role: AgentRole, llm_client, ontology: AccreditationOntology, 
                 audit_system: AuditTrailSystem):
        self.role = role
        self.llm_client = llm_client
        self.ontology = ontology
        self.audit_system = audit_system
        self.agent_id = str(uuid.uuid4())
        
    async def process(self, context: PipelineContext) -> AgentOutput:
        """Process the context and return agent output."""
        raise NotImplementedError("Subclasses must implement process method")
    
    def _create_audit_event(self, context: PipelineContext, event_type: str, 
                           data: Dict[str, Any]) -> None:
        """Create an audit event for traceability."""
        event = AuditEvent(
            event_type=event_type,
            agent_role=self.role.value,
            session_id=context.session_id,
            data=data,
            agent_id=self.agent_id
        )
        self.audit_system.log_event(event)

class MapperAgent(BaseAgent):
    """Agent responsible for classifying artifacts to standards."""
    
    def __init__(self, llm_client, ontology: AccreditationOntology, 
                 audit_system: AuditTrailSystem, matcher: VectorWeightedMatcher):
        super().__init__(AgentRole.MAPPER, llm_client, ontology, audit_system)
        self.matcher = matcher
        
    async def process(self, context: PipelineContext) -> AgentOutput:
        """Map evidence documents to accreditation standards."""
        
        start_time = datetime.utcnow()
        mapped_standards = {}
        total_confidence = 0.0
        match_count = 0
        
        # Map each evidence document to standards
        for evidence in context.evidence_documents:
            
            # Get vector-weighted matches
            matches = self.matcher.match_evidence_to_standards(
                evidence, 
                context.standards_scope,
                MatchingStrategy.EXACT_SEMANTIC
            )
            
            # Enhance matches with LLM reasoning
            enhanced_matches = await self._enhance_matches_with_llm(evidence, matches, context)
            
            mapped_standards[evidence.id] = enhanced_matches
            
            # Track confidence metrics
            for match in enhanced_matches:
                total_confidence += match.confidence_score
                match_count += 1
            
            # Create audit trail
            self._create_audit_event(context, "evidence_mapped", {
                "evidence_id": evidence.id,
                "matches_found": len(enhanced_matches),
                "avg_confidence": np.mean([m.confidence_score for m in enhanced_matches]) if enhanced_matches else 0.0
            })
        
        # Update context
        context.mapped_standards = mapped_standards
        context.current_phase = ProcessingPhase.MAPPING
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        avg_confidence = total_confidence / match_count if match_count > 0 else 0.0
        
        return AgentOutput(
            agent_role=self.role,
            phase=ProcessingPhase.MAPPING,
            output_data={
                "mapped_standards": mapped_standards,
                "total_matches": match_count,
                "avg_confidence": avg_confidence
            },
            confidence_score=avg_confidence,
            processing_time=processing_time,
            input_artifacts=[doc.id for doc in context.evidence_documents]
        )
    
    async def _enhance_matches_with_llm(self, evidence: EvidenceDocument, 
                                      matches: List[StandardMatch],
                                      context: PipelineContext) -> List[StandardMatch]:
        """Enhance vector matches with LLM reasoning."""
        
        if not matches:
            return matches
        
        # Prepare LLM prompt for match validation and enhancement
        prompt = self._build_enhancement_prompt(evidence, matches, context)
        
        try:
            # Call LLM for reasoning
            response = await self.llm_client.generate_completion(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse LLM response and enhance matches
            enhanced_matches = self._parse_enhancement_response(response, matches)
            
            return enhanced_matches
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return matches  # Return original matches on error
    
    def _build_enhancement_prompt(self, evidence: EvidenceDocument, 
                                matches: List[StandardMatch],
                                context: PipelineContext) -> str:
        """Build prompt for LLM match enhancement."""
        
        standards_context = []
        for match in matches[:5]:  # Limit to top 5 matches
            standard = self.ontology.nodes[match.standard_id]
            standards_context.append(f"- {standard.label} (confidence: {match.confidence_score:.3f})")
        
        prompt = f"""
Analyze the following evidence document and validate its mapping to accreditation standards.

EVIDENCE DOCUMENT:
Title: {evidence.title}
Type: {evidence.evidence_type.value}
Content Summary: {evidence.content[:500]}...

ACCREDITOR: {context.accreditor_id}
INSTITUTION TYPE: Based on context

PROPOSED MAPPINGS:
{chr(10).join(standards_context)}

TASK:
1. Validate each proposed mapping (VALID/INVALID/UNCERTAIN)
2. Suggest confidence score adjustments (if any)
3. Identify any missing mappings that should be considered
4. Provide reasoning for your assessments

Respond in JSON format:
{
  "validations": [
    {
      "standard_id": "string",
      "validation": "VALID|INVALID|UNCERTAIN", 
      "confidence_adjustment": 0.0,
      "reasoning": "string"
    }
  ],
  "missing_mappings": ["standard_id1", "standard_id2"],
  "overall_assessment": "string"
}
"""
        return prompt
    
    def _parse_enhancement_response(self, response: str, 
                                  original_matches: List[StandardMatch]) -> List[StandardMatch]:
        """Parse LLM response and enhance matches."""
        
        try:
            response_data = json.loads(response)
            enhanced_matches = []
            
            # Create mapping for quick lookup
            match_map = {match.standard_id: match for match in original_matches}
            
            for validation in response_data.get("validations", []):
                standard_id = validation.get("standard_id")
                if standard_id not in match_map:
                    continue
                
                match = match_map[standard_id]
                validation_result = validation.get("validation", "VALID")
                
                if validation_result == "INVALID":
                    continue  # Skip invalid matches
                
                # Apply confidence adjustment
                adjustment = validation.get("confidence_adjustment", 0.0)
                new_confidence = max(0.0, min(1.0, match.confidence_score + adjustment))
                
                # Create enhanced match
                enhanced_match = StandardMatch(
                    standard_id=match.standard_id,
                    evidence_id=match.evidence_id,
                    confidence_score=new_confidence,
                    match_type=match.match_type,
                    complexity_level=match.complexity_level,
                    semantic_score=match.semantic_score,
                    hierarchy_score=match.hierarchy_score,
                    domain_score=match.domain_score,
                    evidence_score=match.evidence_score,
                    temporal_score=match.temporal_score,
                    matched_concepts=match.matched_concepts,
                    evidence_gaps=match.evidence_gaps,
                    supporting_evidence=match.supporting_evidence + [validation.get("reasoning", "")]
                )
                
                enhanced_matches.append(enhanced_match)
            
            return enhanced_matches
            
        except Exception as e:
            logger.error(f"Failed to parse enhancement response: {e}")
            return original_matches

class GapFinderAgent(BaseAgent):
    """Agent responsible for identifying missing evidence and gaps."""
    
    def __init__(self, llm_client, ontology: AccreditationOntology, audit_system: AuditTrailSystem):
        super().__init__(AgentRole.GAP_FINDER, llm_client, ontology, audit_system)
        
    async def process(self, context: PipelineContext) -> AgentOutput:
        """Identify gaps in evidence coverage."""
        
        start_time = datetime.utcnow()
        
        # Analyze coverage for each standard
        gaps = await self._analyze_evidence_gaps(context)
        
        # Calculate gap severity scores
        severity_scores = self._calculate_gap_severity(gaps, context)
        
        # Generate recommendations
        recommendations = await self._generate_gap_recommendations(gaps, context)
        
        # Update context
        context.identified_gaps = gaps
        context.gap_severity_scores = severity_scores
        context.current_phase = ProcessingPhase.GAP_ANALYSIS
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate overall confidence based on gap analysis
        total_gaps = len(gaps)
        critical_gaps = len([g for g in gaps if severity_scores.get(g.get("gap_id", ""), 0.0) >= 0.8])
        confidence = max(0.0, 1.0 - (critical_gaps / max(1, total_gaps)))
        
        self._create_audit_event(context, "gaps_identified", {
            "total_gaps": total_gaps,
            "critical_gaps": critical_gaps,
            "coverage_score": confidence
        })
        
        return AgentOutput(
            agent_role=self.role,
            phase=ProcessingPhase.GAP_ANALYSIS,
            output_data={
                "identified_gaps": gaps,
                "severity_scores": severity_scores,
                "recommendations": recommendations,
                "coverage_score": confidence
            },
            confidence_score=confidence,
            processing_time=processing_time
        )
    
    async def _analyze_evidence_gaps(self, context: PipelineContext) -> List[Dict[str, Any]]:
        """Analyze gaps in evidence coverage."""
        
        gaps = []
        
        for standard_id in context.standards_scope:
            if standard_id not in self.ontology.nodes:
                continue
            
            standard_node = self.ontology.nodes[standard_id]
            
            # Check if standard has any evidence mapped to it
            has_evidence = any(
                standard_id in [match.standard_id for match in matches]
                for matches in context.mapped_standards.values()
            )
            
            if not has_evidence:
                # Complete gap - no evidence at all
                gap = {
                    "gap_id": str(uuid.uuid4()),
                    "gap_type": "complete_absence",
                    "standard_id": standard_id,
                    "standard_label": standard_node.label,
                    "domain": standard_node.domain.value,
                    "required_evidence_types": [et.value for et in standard_node.required_evidence_types],
                    "description": f"No evidence found for {standard_node.label}",
                    "impact": "critical"
                }
                gaps.append(gap)
            else:
                # Check for evidence type gaps
                mapped_evidence_types = set()
                for evidence_id, matches in context.mapped_standards.items():
                    for match in matches:
                        if match.standard_id == standard_id:
                            # Find the evidence document
                            evidence = next(
                                (e for e in context.evidence_documents if e.id == evidence_id), 
                                None
                            )
                            if evidence:
                                mapped_evidence_types.add(evidence.evidence_type)
                
                required_types = set(standard_node.required_evidence_types)
                missing_types = required_types - mapped_evidence_types
                
                if missing_types:
                    gap = {
                        "gap_id": str(uuid.uuid4()),
                        "gap_type": "evidence_type_gap",
                        "standard_id": standard_id,
                        "standard_label": standard_node.label,
                        "domain": standard_node.domain.value,
                        "missing_evidence_types": [et.value for et in missing_types],
                        "available_evidence_types": [et.value for et in mapped_evidence_types],
                        "description": f"Missing evidence types for {standard_node.label}",
                        "impact": "moderate" if len(missing_types) <= len(mapped_evidence_types) else "high"
                    }
                    gaps.append(gap)
        
        return gaps
    
    def _calculate_gap_severity(self, gaps: List[Dict[str, Any]], 
                               context: PipelineContext) -> Dict[str, float]:
        """Calculate severity scores for identified gaps."""
        
        severity_scores = {}
        
        for gap in gaps:
            gap_id = gap["gap_id"]
            standard_id = gap["standard_id"]
            
            # Base severity based on gap type
            if gap["gap_type"] == "complete_absence":
                base_severity = 0.9
            elif gap["gap_type"] == "evidence_type_gap":
                missing_count = len(gap.get("missing_evidence_types", []))
                available_count = len(gap.get("available_evidence_types", []))
                base_severity = 0.7 * (missing_count / max(1, missing_count + available_count))
            else:
                base_severity = 0.5
            
            # Adjust based on standard criticality
            if standard_id in self.ontology.nodes:
                criticality = self.ontology.nodes[standard_id].compliance_criticality
                base_severity *= criticality
            
            # Adjust based on domain importance (simplified)
            domain_weights = {
                AccreditationDomain.MISSION_GOVERNANCE: 1.0,
                AccreditationDomain.ACADEMIC_PROGRAMS: 0.9,
                AccreditationDomain.STUDENT_SUCCESS: 0.8,
                AccreditationDomain.FACULTY_RESOURCES: 0.8,
                AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS: 0.9,
                AccreditationDomain.FINANCIAL_RESOURCES: 0.7,
                AccreditationDomain.INFRASTRUCTURE: 0.6,
                AccreditationDomain.COMPLIANCE_ETHICS: 0.85
            }
            
            domain_str = gap.get("domain", "")
            try:
                domain = AccreditationDomain(domain_str)
                domain_weight = domain_weights.get(domain, 0.7)
                base_severity *= domain_weight
            except ValueError:
                pass  # Use base severity if domain not found
            
            severity_scores[gap_id] = min(1.0, base_severity)
        
        return severity_scores
    
    async def _generate_gap_recommendations(self, gaps: List[Dict[str, Any]], 
                                          context: PipelineContext) -> List[Dict[str, Any]]:
        """Generate recommendations for addressing gaps."""
        
        recommendations = []
        
        # Group gaps by domain for strategic recommendations
        domain_gaps = {}
        for gap in gaps:
            domain = gap.get("domain", "unknown")
            if domain not in domain_gaps:
                domain_gaps[domain] = []
            domain_gaps[domain].append(gap)
        
        for domain, domain_gap_list in domain_gaps.items():
            if len(domain_gap_list) >= 3:  # Strategic recommendation for multiple gaps
                recommendations.append({
                    "type": "strategic",
                    "domain": domain,
                    "priority": "high",
                    "recommendation": f"Comprehensive evidence collection needed for {domain} domain",
                    "affected_standards": [g["standard_id"] for g in domain_gap_list],
                    "suggested_actions": [
                        f"Conduct {domain} domain assessment",
                        "Review existing documentation",
                        "Interview stakeholders",
                        "Collect supporting artifacts"
                    ]
                })
        
        # Individual gap recommendations
        for gap in gaps:
            if gap["gap_type"] == "complete_absence":
                recommendations.append({
                    "type": "critical",
                    "standard_id": gap["standard_id"],
                    "priority": "critical",
                    "recommendation": f"Urgent: Collect evidence for {gap['standard_label']}",
                    "suggested_evidence_types": gap.get("required_evidence_types", []),
                    "estimated_effort": "high"
                })
        
        return recommendations

class NarratorAgent(BaseAgent):
    """Agent responsible for drafting prose paragraphs and narratives."""
    
    def __init__(self, llm_client, ontology: AccreditationOntology, audit_system: AuditTrailSystem):
        super().__init__(AgentRole.NARRATOR, llm_client, ontology, audit_system)
        
    async def process(self, context: PipelineContext) -> AgentOutput:
        """Generate narrative prose for each accreditation section."""
        
        start_time = datetime.utcnow()
        
        # Generate section narratives
        narratives = await self._generate_section_narratives(context)
        
        # Generate evidence citations
        citations = self._generate_evidence_citations(context)
        
        # Create comprehensive document structure
        document_structure = self._create_document_structure(narratives, citations, context)
        
        # Update context
        context.section_narratives = narratives
        context.evidence_citations = citations
        context.current_phase = ProcessingPhase.NARRATIVE_GENERATION
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate confidence based on narrative completeness
        total_sections = len(context.standards_scope)
        completed_sections = len(narratives)
        confidence = completed_sections / max(1, total_sections)
        
        self._create_audit_event(context, "narratives_generated", {
            "sections_completed": completed_sections,
            "total_sections": total_sections,
            "avg_citation_count": np.mean([len(cites) for cites in citations.values()]) if citations else 0
        })
        
        return AgentOutput(
            agent_role=self.role,
            phase=ProcessingPhase.NARRATIVE_GENERATION,
            output_data={
                "section_narratives": narratives,
                "evidence_citations": citations,
                "document_structure": document_structure
            },
            confidence_score=confidence,
            processing_time=processing_time
        )
    
    async def _generate_section_narratives(self, context: PipelineContext) -> Dict[str, str]:
        """Generate narrative prose for each accreditation section."""
        
        narratives = {}
        
        # Group standards by domain for coherent narratives
        domain_standards = {}
        for standard_id in context.standards_scope:
            if standard_id in self.ontology.nodes:
                domain = self.ontology.nodes[standard_id].domain
                if domain not in domain_standards:
                    domain_standards[domain] = []
                domain_standards[domain].append(standard_id)
        
        # Generate narrative for each domain
        for domain, standards in domain_standards.items():
            narrative = await self._generate_domain_narrative(domain, standards, context)
            narratives[domain.value] = narrative
        
        return narratives
    
    async def _generate_domain_narrative(self, domain: AccreditationDomain, 
                                       standards: List[str], 
                                       context: PipelineContext) -> str:
        """Generate narrative for a specific domain."""
        
        # Collect evidence and matches for this domain
        domain_evidence = []
        domain_matches = []
        
        for evidence in context.evidence_documents:
            for standard_id in standards:
                matches = context.mapped_standards.get(evidence.id, [])
                for match in matches:
                    if match.standard_id == standard_id:
                        domain_evidence.append(evidence)
                        domain_matches.append(match)
        
        # Build narrative prompt
        prompt = self._build_narrative_prompt(domain, standards, domain_evidence, domain_matches, context)
        
        try:
            response = await self.llm_client.generate_completion(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Narrative generation failed for {domain}: {e}")
            return f"Narrative generation failed for {domain.value} domain."
    
    def _build_narrative_prompt(self, domain: AccreditationDomain, standards: List[str],
                               evidence: List[EvidenceDocument], matches: List[StandardMatch],
                               context: PipelineContext) -> str:
        """Build prompt for narrative generation."""
        
        # Prepare evidence summaries
        evidence_summaries = []
        for doc in evidence[:10]:  # Limit for prompt length
            evidence_summaries.append(f"- {doc.title} ({doc.evidence_type.value})")
        
        # Prepare standards information
        standards_info = []
        for standard_id in standards[:10]:  # Limit for prompt length
            if standard_id in self.ontology.nodes:
                node = self.ontology.nodes[standard_id]
                standards_info.append(f"- {node.label}")
        
        # Get gap information for this domain
        domain_gaps = [
            gap for gap in context.identified_gaps 
            if gap.get("domain") == domain.value
        ]
        
        prompt = f"""
Write a comprehensive narrative paragraph for the {domain.value.replace('_', ' ').title()} domain of an accreditation self-study report.

INSTITUTION: {context.institution_id}
ACCREDITOR: {context.accreditor_id}

STANDARDS ADDRESSED:
{chr(10).join(standards_info)}

AVAILABLE EVIDENCE:
{chr(10).join(evidence_summaries)}

IDENTIFIED GAPS: {len(domain_gaps)} gaps identified

REQUIREMENTS:
1. Write in formal academic prose suitable for accreditation reviewers
2. Demonstrate compliance with relevant standards using specific evidence
3. Address any gaps or areas for improvement honestly
4. Include forward-looking statements about continuous improvement
5. Maintain professional, confident tone while being factual
6. Use approximately 300-500 words

The narrative should follow this structure:
- Opening statement about the institution's commitment to this domain
- Description of current practices and evidence of compliance  
- Discussion of assessment and improvement processes
- Acknowledgment of any gaps and plans to address them
- Conclusion emphasizing ongoing commitment to excellence

Write the narrative paragraph:
"""
        
        return prompt
    
    def _generate_evidence_citations(self, context: PipelineContext) -> Dict[str, List[str]]:
        """Generate proper evidence citations for each standard with page numbers."""
        
        citations = {}
        
        for standard_id in context.standards_scope:
            standard_citations = []
            
            # Find all evidence mapped to this standard
            for evidence_id, matches in context.mapped_standards.items():
                for match in matches:
                    if match.standard_id == standard_id and match.confidence_score >= 0.7:
                        # Find the evidence document
                        evidence = next(
                            (e for e in context.evidence_documents if e.id == evidence_id),
                            None
                        )
                        if evidence:
                            # Build citation with page numbers if available
                            citation_parts = [
                                evidence.title,
                                evidence.evidence_type.value,
                                evidence.collection_date.strftime('%Y-%m-%d')
                            ]
                            
                            # Add page numbers if available in the match
                            if hasattr(match, 'page_numbers') and match.page_numbers:
                                if len(match.page_numbers) == 1:
                                    citation_parts.append(f"p. {match.page_numbers[0]}")
                                elif len(match.page_numbers) <= 3:
                                    pages_str = ", ".join(str(p) for p in match.page_numbers)
                                    citation_parts.append(f"pp. {pages_str}")
                                else:
                                    # For many pages, show range
                                    citation_parts.append(f"pp. {match.page_numbers[0]}-{match.page_numbers[-1]}")
                            
                            citation = f"{citation_parts[0]} ({', '.join(citation_parts[1:])})"
                            standard_citations.append(citation)
            
            if standard_citations:
                citations[standard_id] = standard_citations
        
        return citations
    
    def _create_document_structure(self, narratives: Dict[str, str], 
                                  citations: Dict[str, List[str]],
                                  context: PipelineContext) -> Dict[str, Any]:
        """Create overall document structure."""
        
        return {
            "title": f"Accreditation Self-Study Report - {context.institution_id}",
            "accreditor": context.accreditor_id,
            "generation_date": datetime.utcnow().isoformat(),
            "sections": [
                {
                    "domain": domain,
                    "narrative": narrative,
                    "standards_addressed": [
                        std_id for std_id in context.standards_scope
                        if std_id in self.ontology.nodes and 
                        self.ontology.nodes[std_id].domain.value == domain
                    ],
                    "evidence_count": len([
                        evidence for evidence in context.evidence_documents
                        if domain in [tag.value for tag in evidence.domain_tags]
                    ])
                }
                for domain, narrative in narratives.items()
            ],
            "overall_statistics": {
                "total_evidence_documents": len(context.evidence_documents),
                "total_standards_addressed": len(context.standards_scope),
                "total_gaps_identified": len(context.identified_gaps),
                "avg_confidence_score": np.mean([
                    match.confidence_score
                    for matches in context.mapped_standards.values()
                    for match in matches
                ]) if context.mapped_standards else 0.0
            }
        }

class VerifierAgent(BaseAgent):
    """Agent responsible for verifying citations and ensuring ≥0.85 cosine similarity."""
    
    def __init__(self, llm_client, ontology: AccreditationOntology, 
                 audit_system: AuditTrailSystem, matcher: VectorWeightedMatcher):
        super().__init__(AgentRole.VERIFIER, llm_client, ontology, audit_system)
        self.matcher = matcher
        self.cosine_threshold = 0.85
        
    async def process(self, context: PipelineContext) -> AgentOutput:
        """Verify citations and ensure semantic alignment."""
        
        start_time = datetime.utcnow()
        
        # Verify all citations
        verification_results = await self._verify_all_citations(context)
        
        # Calculate overall verification score
        overall_score = self._calculate_overall_verification_score(verification_results)
        
        # Generate verification report
        verification_report = self._generate_verification_report(verification_results, context)
        
        # Update context
        context.citation_verifications = verification_results
        context.overall_verification_score = overall_score
        context.current_phase = ProcessingPhase.VERIFICATION
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        self._create_audit_event(context, "citations_verified", {
            "total_citations": len(verification_results),
            "passed_verifications": len([v for v in verification_results.values() if v.get("passed", False)]),
            "overall_score": overall_score
        })
        
        return AgentOutput(
            agent_role=self.role,
            phase=ProcessingPhase.VERIFICATION,
            output_data={
                "verification_results": verification_results,
                "overall_score": overall_score,
                "verification_report": verification_report
            },
            confidence_score=overall_score,
            processing_time=processing_time
        )
    
    async def _verify_all_citations(self, context: PipelineContext) -> Dict[str, Dict[str, Any]]:
        """Verify all citations in the context."""
        
        verification_results = {}
        
        for standard_id, citations in context.evidence_citations.items():
            standard_verifications = []
            
            for citation in citations:
                verification = await self._verify_single_citation(citation, standard_id, context)
                standard_verifications.append(verification)
            
            verification_results[standard_id] = {
                "citation_count": len(citations),
                "verifications": standard_verifications,
                "passed_count": len([v for v in standard_verifications if v.get("passed", False)]),
                "avg_similarity": np.mean([v.get("cosine_similarity", 0.0) for v in standard_verifications]) if standard_verifications else 0.0,
                "passed": all(v.get("passed", False) for v in standard_verifications)
            }
        
        return verification_results
    
    async def _verify_single_citation(self, citation: str, standard_id: str, 
                                     context: PipelineContext) -> Dict[str, Any]:
        """Verify a single citation against the standard."""
        
        # Find the evidence document for this citation
        evidence_doc = None
        for evidence in context.evidence_documents:
            if evidence.title in citation:
                evidence_doc = evidence
                break
        
        if not evidence_doc:
            return {
                "citation": citation,
                "passed": False,
                "cosine_similarity": 0.0,
                "error": "Evidence document not found"
            }
        
        # Get standard embedding
        if standard_id not in self.ontology.nodes:
            return {
                "citation": citation,
                "passed": False,
                "cosine_similarity": 0.0,
                "error": "Standard not found in ontology"
            }
        
        standard_node = self.ontology.nodes[standard_id]
        if standard_node.embedding_vector is None:
            return {
                "citation": citation,
                "passed": False,
                "cosine_similarity": 0.0,
                "error": "Standard embedding not available"
            }
        
        # Calculate cosine similarity
        cosine_sim = 1 - cosine(evidence_doc.content_embedding, standard_node.embedding_vector)
        
        # Verify against threshold
        passed = cosine_sim >= self.cosine_threshold
        
        # Additional semantic verification using LLM
        llm_verification = await self._llm_verify_citation(citation, standard_id, evidence_doc, context)
        
        return {
            "citation": citation,
            "evidence_id": evidence_doc.id,
            "standard_id": standard_id,
            "cosine_similarity": cosine_sim,
            "threshold": self.cosine_threshold,
            "passed": passed,
            "llm_verification": llm_verification,
            "final_passed": passed and llm_verification.get("verified", False)
        }
    
    async def _llm_verify_citation(self, citation: str, standard_id: str,
                                  evidence: EvidenceDocument, context: PipelineContext) -> Dict[str, Any]:
        """Use LLM to verify semantic alignment of citation."""
        
        standard_node = self.ontology.nodes[standard_id]
        
        prompt = f"""
Verify the semantic alignment between the following evidence and accreditation standard.

STANDARD:
{standard_node.label}
Domain: {standard_node.domain.value}

EVIDENCE:
Title: {evidence.title}
Type: {evidence.evidence_type.value}
Content: {evidence.content[:1000]}...

TASK:
Analyze whether this evidence genuinely supports compliance with the given standard.
Consider:
1. Direct relevance to the standard's requirements
2. Quality and reliability of the evidence
3. Completeness of coverage
4. Potential gaps or limitations

Respond in JSON format:
{
  "verified": true/false,
  "relevance_score": 0.0-1.0,
  "quality_assessment": "string",
  "coverage_assessment": "string", 
  "limitations": ["string"],
  "recommendations": ["string"]
}
"""
        
        try:
            response = await self.llm_client.generate_completion(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1
            )
            
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"LLM verification failed: {e}")
            return {"verified": False, "error": str(e)}
    
    def _calculate_overall_verification_score(self, verification_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall verification score."""
        
        if not verification_results:
            return 0.0
        
        total_citations = 0
        passed_citations = 0
        total_similarity = 0.0
        
        for standard_result in verification_results.values():
            verifications = standard_result.get("verifications", [])
            for verification in verifications:
                total_citations += 1
                if verification.get("final_passed", False):
                    passed_citations += 1
                total_similarity += verification.get("cosine_similarity", 0.0)
        
        if total_citations == 0:
            return 0.0
        
        # Weighted score: 70% pass rate, 30% average similarity
        pass_rate = passed_citations / total_citations
        avg_similarity = total_similarity / total_citations
        
        return 0.7 * pass_rate + 0.3 * avg_similarity
    
    def _generate_verification_report(self, verification_results: Dict[str, Dict[str, Any]],
                                    context: PipelineContext) -> Dict[str, Any]:
        """Generate comprehensive verification report."""
        
        total_standards = len(verification_results)
        passed_standards = len([r for r in verification_results.values() if r.get("passed", False)])
        
        # Identify problematic citations
        problematic_citations = []
        for standard_id, result in verification_results.items():
            for verification in result.get("verifications", []):
                if not verification.get("final_passed", False):
                    problematic_citations.append({
                        "standard_id": standard_id,
                        "citation": verification.get("citation", ""),
                        "cosine_similarity": verification.get("cosine_similarity", 0.0),
                        "issues": verification.get("llm_verification", {}).get("limitations", [])
                    })
        
        return {
            "summary": {
                "total_standards_verified": total_standards,
                "standards_passed": passed_standards,
                "pass_rate": passed_standards / max(1, total_standards),
                "overall_verification_score": context.overall_verification_score
            },
            "problematic_citations": problematic_citations,
            "recommendations": self._generate_verification_recommendations(problematic_citations),
            "verification_timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_verification_recommendations(self, problematic_citations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on verification results."""
        
        recommendations = []
        
        if len(problematic_citations) > 0:
            recommendations.append(f"Review {len(problematic_citations)} problematic citations")
        
        low_similarity_citations = [c for c in problematic_citations if c["cosine_similarity"] < 0.7]
        if low_similarity_citations:
            recommendations.append("Strengthen evidence alignment for low-similarity citations")
        
        if len(problematic_citations) / max(1, len(problematic_citations)) > 0.2:
            recommendations.append("Consider comprehensive evidence review and collection")
        
        return recommendations

class MultiAgentPipeline:
    """Main orchestrator for the four-agent pipeline."""
    
    def __init__(self, llm_client, ontology: AccreditationOntology, 
                 matcher: VectorWeightedMatcher, audit_system: AuditTrailSystem):
        
        self.llm_client = llm_client
        self.ontology = ontology
        self.matcher = matcher
        self.audit_system = audit_system
        
        # Initialize agents
        self.mapper = MapperAgent(llm_client, ontology, audit_system, matcher)
        self.gap_finder = GapFinderAgent(llm_client, ontology, audit_system)
        self.narrator = NarratorAgent(llm_client, ontology, audit_system)
        self.verifier = VerifierAgent(llm_client, ontology, audit_system, matcher)
        
    async def process_full_pipeline(self, context: PipelineContext) -> PipelineContext:
        """Execute the complete four-agent pipeline."""
        
        # Log pipeline start
        self.audit_system.log_event(AuditEvent(
            event_type="pipeline_started",
            session_id=context.session_id,
            data={
                "institution_id": context.institution_id,
                "accreditor_id": context.accreditor_id,
                "evidence_count": len(context.evidence_documents),
                "standards_count": len(context.standards_scope)
            }
        ))
        
        try:
            # Phase 1: Mapping
            mapper_output = await self.mapper.process(context)
            context.agent_outputs.append(mapper_output)
            
            # Phase 2: Gap Analysis
            gap_finder_output = await self.gap_finder.process(context)
            context.agent_outputs.append(gap_finder_output)
            
            # Phase 3: Narrative Generation
            narrator_output = await self.narrator.process(context)
            context.agent_outputs.append(narrator_output)
            
            # Phase 4: Verification
            verifier_output = await self.verifier.process(context)
            context.agent_outputs.append(verifier_output)
            
            # Finalize
            context.current_phase = ProcessingPhase.FINALIZATION
            
            # Log pipeline completion
            self.audit_system.log_event(AuditEvent(
                event_type="pipeline_completed",
                session_id=context.session_id,
                data={
                    "total_processing_time": sum(output.processing_time for output in context.agent_outputs),
                    "final_verification_score": context.overall_verification_score,
                    "gaps_identified": len(context.identified_gaps)
                }
            ))
            
        except Exception as e:
            # Log pipeline error
            self.audit_system.log_event(AuditEvent(
                event_type="pipeline_error",
                session_id=context.session_id,
                data={"error": str(e), "phase": context.current_phase.value}
            ))
            raise
        
        return context
    
    async def process_parallel_phases(self, context: PipelineContext) -> PipelineContext:
        """Execute pipeline with parallel processing where possible."""
        
        # Phase 1: Mapping (must be first)
        mapper_output = await self.mapper.process(context)
        context.agent_outputs.append(mapper_output)
        
        # Phase 2 & 3: Gap Analysis and Narrative Generation (can be parallel)
        gap_task = asyncio.create_task(self.gap_finder.process(context))
        narrator_task = asyncio.create_task(self.narrator.process(context))
        
        gap_output, narrator_output = await asyncio.gather(gap_task, narrator_task)
        context.agent_outputs.extend([gap_output, narrator_output])
        
        # Phase 4: Verification (must be last)
        verifier_output = await self.verifier.process(context)
        context.agent_outputs.append(verifier_output)
        
        context.current_phase = ProcessingPhase.FINALIZATION
        
        return context
