"""
AutoGen Agent Framework for A3E

Implements the four-agent workflow: Mapper → GapFinder → Narrator → Verifier
Supports all US accrediting bodies with institution-type contextualization.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional AutoGen imports
try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available - agent workflows disabled")
    
    # Mock classes for type hints
    class AssistantAgent:
        def __init__(self, *args, **kwargs):
            pass
    
    class UserProxyAgent:
        def __init__(self, *args, **kwargs):
            pass
    
    class GroupChat:
        def __init__(self, *args, **kwargs):
            pass
    
    class GroupChatManager:
        def __init__(self, *args, **kwargs):
            pass

from ..core.config import settings
from ..core.accreditation_registry import ALL_ACCREDITORS, get_standards_by_accreditor_and_institution_type
from ..models import Institution, Standard, Evidence, AgentWorkflow, ProcessingStatus
from ..services.vector_service import VectorService
from ..services.llm_service import LLMService


@dataclass
class AgentResult:
    """Standardized agent result format"""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    confidence_score: float
    execution_time: float
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


class MapperAgent:
    """Agent responsible for mapping evidence to standards"""
    
    def __init__(self, llm_service: LLMService, vector_service: Optional[VectorService] = None):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.agent = AssistantAgent(
            name="Mapper",
            system_message=self._get_system_message(),
            llm_config={
                "model": settings.bedrock_model_id,
                "temperature": settings.agent_temperature,
                "max_tokens": settings.bedrock_max_tokens
            }
        )
    
    def _get_system_message(self) -> str:
        return """
        You are the Mapper Agent in the A3E system, specialized in mapping institutional evidence to accreditation standards.
        
        Your responsibilities:
        1. Analyze evidence artifacts (documents, data, policies) for content and context
        2. Match evidence to specific accreditation standards using semantic similarity
        3. Assign confidence scores (0.0-1.0) for each evidence-standard mapping
        4. Consider institution type context when making mappings
        5. Return structured JSON output with mappings and confidence scores
        
        Key principles:
        - Only map evidence that clearly supports a standard (>0.7 confidence)
        - Consider the specific accreditor's language and requirements
        - Account for institution type (community college vs university vs specialized)
        - Provide reasoning for each mapping decision
        - Flag ambiguous cases for human review
        
        Output format:
        {
            "mappings": [
                {
                    "evidence_id": "uuid",
                    "standard_id": "msche_1",
                    "confidence_score": 0.85,
                    "reasoning": "Document explicitly addresses mission statement requirements",
                    "relevant_excerpts": ["excerpt1", "excerpt2"]
                }
            ],
            "unmapped_evidence": ["uuid1", "uuid2"],
            "flagged_for_review": ["uuid3"],
            "overall_confidence": 0.82
        }
        """
    
    async def map_evidence_to_standards(
        self,
        evidence_items: List[Evidence],
        standards: List[Standard],
        institution: Institution
    ) -> AgentResult:
        """Map evidence items to relevant standards"""
        start_time = datetime.now()
        
        try:
            # Prepare context for the agent
            context = {
                "institution": {
                    "name": institution.name,
                    "types": institution.institution_types,
                    "state": institution.state,
                    "enrollment": institution.total_enrollment
                },
                "evidence_items": [
                    {
                        "id": str(evidence.id),
                        "title": evidence.title,
                        "type": evidence.evidence_type.value,
                        "description": evidence.description,
                        "extracted_text": evidence.extracted_text[:2000] if evidence.extracted_text else "",
                        "keywords": evidence.keywords
                    }
                    for evidence in evidence_items
                ],
                "standards": [
                    {
                        "id": standard.id,
                        "title": standard.title,
                        "description": standard.description,
                        "evidence_requirements": standard.evidence_requirements,
                        "applicable_types": standard.applicable_institution_types
                    }
                    for standard in standards
                ]
            }
            
            # Use vector similarity for initial filtering
            similar_mappings = await self._find_similar_evidence_standard_pairs(
                evidence_items, standards
            )
            
            # Generate agent response
            prompt = f"""
            Map the following evidence to appropriate standards for {institution.name}.
            
            Institution Context: {json.dumps(context['institution'], indent=2)}
            
            Evidence to Map: {json.dumps(context['evidence_items'], indent=2)}
            
            Available Standards: {json.dumps(context['standards'], indent=2)}
            
            Vector Similarity Suggestions: {json.dumps(similar_mappings, indent=2)}
            
            Provide detailed mappings with confidence scores and reasoning.
            """
            
            response = await self.llm_service.generate_response(prompt, "mapper")
            
            # Parse and validate response
            mapping_data = self._parse_mapping_response(response)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name="Mapper",
                success=True,
                data=mapping_data,
                confidence_score=mapping_data.get("overall_confidence", 0.0),
                execution_time=execution_time,
                token_usage=getattr(response, 'token_usage', None)
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                agent_name="Mapper",
                success=False,
                data={},
                confidence_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def _find_similar_evidence_standard_pairs(
        self,
        evidence_items: List[Evidence],
        standards: List[Standard]
    ) -> List[Dict[str, Any]]:
        """Use vector similarity to suggest evidence-standard pairs"""
        suggestions = []
        
        for evidence in evidence_items:
            if evidence.embedding_vector:
                # Find most similar standards
                similar_standards = await self.vector_service.find_similar_standards(
                    evidence.embedding_vector,
                    [s.id for s in standards],
                    top_k=3
                )
                
                for standard_id, similarity in similar_standards:
                    if similarity > 0.7:  # Threshold for consideration
                        suggestions.append({
                            "evidence_id": str(evidence.id),
                            "standard_id": standard_id,
                            "similarity_score": similarity,
                            "suggestion_type": "vector_similarity"
                        })
        
        return suggestions
    
    def _parse_mapping_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate agent response"""
        try:
            data = json.loads(response)
            
            # Validate required fields
            required_fields = ["mappings", "unmapped_evidence", "overall_confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate mapping structure
            for mapping in data.get("mappings", []):
                required_mapping_fields = ["evidence_id", "standard_id", "confidence_score"]
                for field in required_mapping_fields:
                    if field not in mapping:
                        raise ValueError(f"Missing required mapping field: {field}")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")


class GapFinderAgent:
    """Agent responsible for identifying evidence gaps"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.agent = AssistantAgent(
            name="GapFinder",
            system_message=self._get_system_message(),
            llm_config={
                "model": settings.bedrock_model_id,
                "temperature": settings.agent_temperature,
                "max_tokens": settings.bedrock_max_tokens
            }
        )
    
    def _get_system_message(self) -> str:
        return """
        You are the GapFinder Agent in the A3E system, specialized in identifying evidence gaps for accreditation standards.
        
        Your responsibilities:
        1. Analyze the mapping between evidence and standards
        2. Identify standards with no evidence (Red - Critical gaps)
        3. Identify standards with insufficient evidence (Amber - Needs attention)
        4. Identify standards with adequate evidence (Green - Compliant)
        5. Prioritize gaps based on accreditor importance and institution context
        6. Suggest specific evidence types needed to fill gaps
        
        Gap Classification:
        - RED: No evidence mapped to standard (critical risk)
        - AMBER: Some evidence but insufficient for compliance (moderate risk)
        - GREEN: Adequate evidence for compliance (low risk)
        
        Output format:
        {
            "gap_summary": {
                "total_standards": 25,
                "red_gaps": 3,
                "amber_gaps": 7, 
                "green_compliant": 15
            },
            "detailed_gaps": [
                {
                    "standard_id": "msche_1",
                    "status": "RED",
                    "risk_level": "HIGH",
                    "current_evidence_count": 0,
                    "required_evidence_types": ["mission_statement", "board_minutes"],
                    "recommendations": ["Locate and digitize mission statement", "Request board minutes from governance"],
                    "priority": 1
                }
            ],
            "recommendations": {
                "immediate_actions": ["action1", "action2"],
                "long_term_strategies": ["strategy1", "strategy2"]
            }
        }
        """
    
    async def analyze_gaps(
        self,
        mapping_result: Dict[str, Any],
        standards: List[Standard],
        institution: Institution,
        accreditor_id: str
    ) -> AgentResult:
        """Analyze evidence gaps for standards"""
        start_time = datetime.now()
        
        try:
            # Prepare gap analysis context
            mapped_standards = set()
            evidence_counts = {}
            
            for mapping in mapping_result.get("mappings", []):
                standard_id = mapping["standard_id"]
                mapped_standards.add(standard_id)
                evidence_counts[standard_id] = evidence_counts.get(standard_id, 0) + 1
            
            # Build context for analysis
            context = {
                "institution": {
                    "name": institution.name,
                    "types": institution.institution_types,
                    "enrollment": institution.total_enrollment
                },
                "accreditor": accreditor_id,
                "standards_analysis": [
                    {
                        "id": standard.id,
                        "title": standard.title,
                        "evidence_requirements": standard.evidence_requirements,
                        "weight": standard.weight,
                        "current_evidence_count": evidence_counts.get(standard.id, 0),
                        "is_mapped": standard.id in mapped_standards
                    }
                    for standard in standards
                ],
                "mapping_result": mapping_result
            }
            
            prompt = f"""
            Analyze evidence gaps for {institution.name} seeking {accreditor_id} accreditation.
            
            Context: {json.dumps(context, indent=2)}
            
            Provide a comprehensive gap analysis with prioritized recommendations.
            Focus on institutional context and accreditor-specific requirements.
            """
            
            response = await self.llm_service.generate_response(prompt, "gap_finder")
            gap_data = json.loads(response)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name="GapFinder",
                success=True,
                data=gap_data,
                confidence_score=self._calculate_gap_confidence(gap_data),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                agent_name="GapFinder",
                success=False,
                data={},
                confidence_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _calculate_gap_confidence(self, gap_data: Dict[str, Any]) -> float:
        """Calculate confidence score for gap analysis"""
        total_standards = gap_data.get("gap_summary", {}).get("total_standards", 1)
        detailed_gaps = len(gap_data.get("detailed_gaps", []))
        
        # Higher confidence when more detailed analysis is provided
        return min(0.95, detailed_gaps / total_standards + 0.5)


class NarratorAgent:
    """Agent responsible for generating narrative text"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.agent = AssistantAgent(
            name="Narrator",
            system_message=self._get_system_message(),
            llm_config={
                "model": settings.bedrock_model_id,
                "temperature": 0.2,  # Lower temperature for more consistent narrative
                "max_tokens": settings.bedrock_max_tokens
            }
        )
    
    def _get_system_message(self) -> str:
        return """
        You are the Narrator Agent in the A3E system, specialized in generating compliance narrative text for accreditation self-studies.
        
        Your responsibilities:
        1. Generate clear, professional narrative text for each standard
        2. Incorporate evidence citations naturally within the text
        3. Follow accreditor-specific writing styles and expectations
        4. Ensure narrative addresses all aspects of the standard
        5. Maintain institutional voice and context throughout
        
        Writing Guidelines:
        - Use active voice and clear, direct language
        - Begin each standard with a strong declarative statement
        - Integrate evidence citations seamlessly: "As documented in [1], the institution..."
        - Address the standard comprehensively while staying focused
        - Maintain professional academic tone appropriate for accreditors
        - Include specific data and examples when available
        
        Output format:
        {
            "narratives": [
                {
                    "standard_id": "msche_1",
                    "title": "Mission and Goals",
                    "content": "Full narrative text with [citation] markers...",
                    "citations": [
                        {
                            "id": 1,
                            "evidence_id": "uuid",
                            "title": "Strategic Plan 2024-2029",
                            "excerpt": "Relevant text excerpt",
                            "page_number": "p. 15"
                        }
                    ],
                    "word_count": 450,
                    "completeness_score": 0.92
                }
            ]
        }
        """
    
    async def generate_narratives(
        self,
        mapping_result: Dict[str, Any],
        evidence_items: List[Evidence],
        standards: List[Standard],
        institution: Institution,
        accreditor_id: str
    ) -> AgentResult:
        """Generate narrative text for standards with evidence"""
        start_time = datetime.now()
        
        try:
            # Group evidence by standard
            evidence_by_standard = {}
            for mapping in mapping_result.get("mappings", []):
                standard_id = mapping["standard_id"]
                evidence_id = mapping["evidence_id"]
                
                if standard_id not in evidence_by_standard:
                    evidence_by_standard[standard_id] = []
                
                # Find the evidence item
                evidence_item = next(
                    (e for e in evidence_items if str(e.id) == evidence_id),
                    None
                )
                if evidence_item:
                    evidence_by_standard[standard_id].append({
                        "evidence": evidence_item,
                        "confidence": mapping.get("confidence_score", 0.0),
                        "reasoning": mapping.get("reasoning", ""),
                        "excerpts": mapping.get("relevant_excerpts", [])
                    })
            
            # Generate narratives for standards with evidence
            narratives = []
            for standard in standards:
                if standard.id in evidence_by_standard:
                    narrative = await self._generate_standard_narrative(
                        standard,
                        evidence_by_standard[standard.id],
                        institution,
                        accreditor_id
                    )
                    if narrative:
                        narratives.append(narrative)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name="Narrator",
                success=True,
                data={"narratives": narratives},
                confidence_score=self._calculate_narrative_confidence(narratives),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                agent_name="Narrator",
                success=False,
                data={},
                confidence_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def _generate_standard_narrative(
        self,
        standard: Standard,
        evidence_mappings: List[Dict[str, Any]],
        institution: Institution,
        accreditor_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate narrative for a single standard"""
        
        context = {
            "institution": {
                "name": institution.name,
                "types": institution.institution_types,
                "state": institution.state
            },
            "standard": {
                "id": standard.id,
                "title": standard.title,
                "description": standard.description,
                "requirements": standard.evidence_requirements
            },
            "evidence": [
                {
                    "title": mapping["evidence"].title,
                    "type": mapping["evidence"].evidence_type.value,
                    "description": mapping["evidence"].description,
                    "excerpts": mapping.get("excerpts", []),
                    "confidence": mapping.get("confidence", 0.0)
                }
                for mapping in evidence_mappings
            ],
            "accreditor": accreditor_id
        }
        
        prompt = f"""
        Generate a comprehensive narrative for {standard.title} (Standard {standard.id}) 
        for {institution.name}'s {accreditor_id} accreditation self-study.
        
        Standard Context: {json.dumps(context, indent=2)}
        
        The narrative should:
        1. Directly address the standard requirements
        2. Incorporate all relevant evidence with proper citations
        3. Demonstrate compliance clearly and convincingly
        4. Maintain appropriate academic tone for {accreditor_id}
        5. Be approximately 300-500 words
        
        Include citation numbers [1], [2], etc. for evidence references.
        """
        
        response = await self.llm_service.generate_response(prompt, "narrator")
        
        try:
            narrative_data = json.loads(response)
            return narrative_data
        except json.JSONDecodeError:
            # If not JSON, treat as plain text narrative
            return {
                "standard_id": standard.id,
                "title": standard.title,
                "content": response,
                "citations": self._extract_citations(response, evidence_mappings),
                "word_count": len(response.split()),
                "completeness_score": 0.8  # Default score
            }
    
    def _extract_citations(self, text: str, evidence_mappings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citation information from narrative text"""
        citations = []
        for i, mapping in enumerate(evidence_mappings, 1):
            citations.append({
                "id": i,
                "evidence_id": str(mapping["evidence"].id),
                "title": mapping["evidence"].title,
                "excerpt": mapping.get("excerpts", [""])[0] if mapping.get("excerpts") else "",
                "page_number": "TBD"  # Would need document processing to extract
            })
        return citations
    
    def _calculate_narrative_confidence(self, narratives: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for generated narratives"""
        if not narratives:
            return 0.0
        
        avg_completeness = sum(n.get("completeness_score", 0.5) for n in narratives) / len(narratives)
        return avg_completeness


class VerifierAgent:
    """Agent responsible for verifying citations and narrative accuracy"""
    
    def __init__(self, llm_service: LLMService, vector_service: Optional[VectorService] = None):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.agent = AssistantAgent(
            name="Verifier",
            system_message=self._get_system_message(),
            llm_config={
                "model": settings.bedrock_model_id,
                "temperature": 0.1,  # Very low temperature for verification
                "max_tokens": settings.bedrock_max_tokens
            }
        )
    
    def _get_system_message(self) -> str:
        return """
        You are the Verifier Agent in the A3E system, specialized in verifying citation accuracy and narrative quality.
        
        Your responsibilities:
        1. Verify that citations accurately support narrative claims
        2. Check for factual accuracy against source evidence
        3. Ensure narrative completeness for each standard
        4. Identify any unsupported claims or potential inaccuracies
        5. Recommend revisions when verification fails
        
        Verification Criteria:
        - Citation accuracy: Does the cited evidence actually support the claim?
        - Factual consistency: Are facts and figures accurately represented?
        - Completeness: Does the narrative address all aspects of the standard?
        - Quality: Is the writing clear, professional, and appropriate?
        
        Confidence Threshold: Only approve narratives with ≥85% verification confidence.
        
        Output format:
        {
            "verification_results": [
                {
                    "narrative_id": "standard_id",
                    "overall_score": 0.92,
                    "citation_accuracy": 0.95,
                    "factual_accuracy": 0.88,
                    "completeness": 0.93,
                    "verified": true,
                    "issues_found": [],
                    "recommendations": []
                }
            ],
            "summary": {
                "total_narratives": 15,
                "verified_narratives": 13,
                "needs_revision": 2,
                "overall_confidence": 0.87
            }
        }
        """
    
    async def verify_narratives(
        self,
        narratives: List[Dict[str, Any]],
        evidence_items: List[Evidence],
        standards: List[Standard]
    ) -> AgentResult:
        """Verify accuracy and quality of generated narratives"""
        start_time = datetime.now()
        
        try:
            verification_results = []
            
            for narrative in narratives:
                result = await self._verify_single_narrative(
                    narrative,
                    evidence_items,
                    standards
                )
                verification_results.append(result)
            
            # Calculate summary statistics
            total_narratives = len(verification_results)
            verified_count = sum(1 for r in verification_results if r.get("verified", False))
            overall_confidence = (
                sum(r.get("overall_score", 0.0) for r in verification_results) / total_narratives
                if total_narratives > 0 else 0.0
            )
            
            summary = {
                "total_narratives": total_narratives,
                "verified_narratives": verified_count,
                "needs_revision": total_narratives - verified_count,
                "overall_confidence": overall_confidence
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name="Verifier",
                success=True,
                data={
                    "verification_results": verification_results,
                    "summary": summary
                },
                confidence_score=overall_confidence,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                agent_name="Verifier",
                success=False,
                data={},
                confidence_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def _verify_single_narrative(
        self,
        narrative: Dict[str, Any],
        evidence_items: List[Evidence],
        standards: List[Standard]
    ) -> Dict[str, Any]:
        """Verify a single narrative against evidence and standards"""
        
        standard_id = narrative.get("standard_id")
        content = narrative.get("content", "")
        citations = narrative.get("citations", [])
        
        # Find the relevant standard
        standard = next((s for s in standards if s.id == standard_id), None)
        if not standard:
            return {
                "narrative_id": standard_id,
                "overall_score": 0.0,
                "verified": False,
                "issues_found": ["Standard not found"],
                "recommendations": ["Verify standard ID"]
            }
        
        # Verify each citation
        citation_scores = []
        issues = []
        recommendations = []
        
        for citation in citations:
            evidence_id = citation.get("evidence_id")
            evidence_item = next(
                (e for e in evidence_items if str(e.id) == evidence_id),
                None
            )
            
            if evidence_item:
                # Use vector similarity to verify citation accuracy
                similarity = await self.vector_service.verify_citation_accuracy(
                    content,
                    evidence_item.extracted_text or "",
                    citation.get("excerpt", "")
                )
                citation_scores.append(similarity)
                
                if similarity < settings.citation_threshold:
                    issues.append(f"Low citation accuracy for {citation.get('title', 'Unknown')}: {similarity:.2f}")
                    recommendations.append(f"Review citation for {citation.get('title', 'evidence')}")
            else:
                citation_scores.append(0.0)
                issues.append(f"Evidence not found: {evidence_id}")
                recommendations.append("Verify evidence IDs")
        
        # Calculate scores
        citation_accuracy = sum(citation_scores) / len(citation_scores) if citation_scores else 0.0
        factual_accuracy = 0.85  # Placeholder - would need more sophisticated fact checking
        completeness = min(1.0, len(content.split()) / 400)  # Target ~400 words
        
        overall_score = (citation_accuracy * 0.4 + factual_accuracy * 0.3 + completeness * 0.3)
        verified = overall_score >= settings.citation_threshold and not issues
        
        return {
            "narrative_id": standard_id,
            "overall_score": overall_score,
            "citation_accuracy": citation_accuracy,
            "factual_accuracy": factual_accuracy,
            "completeness": completeness,
            "verified": verified,
            "issues_found": issues,
            "recommendations": recommendations
        }


class A3EAgentOrchestrator:
    """Main orchestrator for the four-agent workflow"""
    
    def __init__(self, llm_service: LLMService, vector_service: Optional[VectorService] = None):
        self.llm_service = llm_service
        self.vector_service = vector_service
        
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen not available - agent workflows will use simplified fallback")
            # Initialize simplified agents without AutoGen
            self.mapper = None
            self.gap_finder = None  
            self.narrator = None
            self.verifier = None
            return
        
        # Initialize agents (some may work without vector service)
        self.mapper = MapperAgent(llm_service, vector_service) if vector_service else None
        self.gap_finder = GapFinderAgent(llm_service)
        self.narrator = NarratorAgent(llm_service)
        self.verifier = VerifierAgent(llm_service, vector_service) if vector_service else None
    
    async def execute_workflow(
        self,
        institution: Institution,
        accreditor_id: str,
        evidence_items: List[Evidence],
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """Execute the complete four-agent workflow"""
        
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen not available - returning simplified workflow result")
            return {
                "workflow_id": f"simplified_{institution.id}_{accreditor_id}",
                "status": "limited",
                "message": "Agent workflows require AutoGen library",
                "institution_id": str(institution.id),
                "accreditor_id": accreditor_id,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "rounds": []
            }
        
        workflow_id = f"workflow_{institution.id}_{accreditor_id}_{datetime.now().isoformat()}"
        
        # Get applicable standards for institution
        institution_types = [InstitutionType(t) for t in institution.institution_types]
        all_standards = []
        for inst_type in institution_types:
            standards = get_standards_by_accreditor_and_institution_type(accreditor_id, inst_type)
            all_standards.extend(standards)
        
        # Remove duplicates
        unique_standards = {s.id: s for s in all_standards}.values()
        standards = list(unique_standards)
        
        results = {
            "workflow_id": workflow_id,
            "institution_id": str(institution.id),
            "accreditor_id": accreditor_id,
            "start_time": datetime.now().isoformat(),
            "rounds": []
        }
        
        current_mapping = None
        current_narratives = None
        
        for round_num in range(1, max_rounds + 1):
            round_start = datetime.now()
            round_results = {"round": round_num, "agents": []}
            
            # Step 1: Mapper Agent
            if round_num == 1 or not current_mapping:
                mapper_result = await self.mapper.map_evidence_to_standards(
                    evidence_items, standards, institution
                )
                round_results["agents"].append(mapper_result)
                
                if mapper_result.success:
                    current_mapping = mapper_result.data
                else:
                    break
            
            # Step 2: GapFinder Agent
            gap_result = await self.gap_finder.analyze_gaps(
                current_mapping, standards, institution, accreditor_id
            )
            round_results["agents"].append(gap_result)
            
            if not gap_result.success:
                break
            
            # Step 3: Narrator Agent (only for standards with evidence)
            narrator_result = await self.narrator.generate_narratives(
                current_mapping, evidence_items, standards, institution, accreditor_id
            )
            round_results["agents"].append(narrator_result)
            
            if narrator_result.success:
                current_narratives = narrator_result.data["narratives"]
            else:
                break
            
            # Step 4: Verifier Agent
            verifier_result = await self.verifier.verify_narratives(
                current_narratives, evidence_items, standards
            )
            round_results["agents"].append(verifier_result)
            
            if not verifier_result.success:
                break
            
            # Check if verification passed
            verification_summary = verifier_result.data.get("summary", {})
            overall_confidence = verification_summary.get("overall_confidence", 0.0)
            
            round_results["round_summary"] = {
                "duration_seconds": (datetime.now() - round_start).total_seconds(),
                "overall_confidence": overall_confidence,
                "converged": overall_confidence >= settings.citation_threshold
            }
            
            results["rounds"].append(round_results)
            
            # Check for convergence
            if overall_confidence >= settings.citation_threshold:
                break
        
        results["end_time"] = datetime.now().isoformat()
        results["final_results"] = {
            "mapping": current_mapping,
            "gap_analysis": gap_result.data if gap_result.success else None,
            "narratives": current_narratives,
            "verification": verifier_result.data if verifier_result.success else None
        }
        
        return results
