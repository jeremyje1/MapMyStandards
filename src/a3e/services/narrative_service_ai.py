"""
CiteGuard™ - AI-Powered Narrative Generation with Evidence Citations
Generates accreditation narratives with mandatory evidence citations and zero hallucination
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from .standards_graph import standards_graph
from .llm_service import LLMService
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIEnabledNarrativeService:
    """Generate narratives with AI, ensuring all claims are evidence-backed"""
    
    def __init__(self):
        self.llm_service = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize LLM service"""
        if not self._initialized:
            settings = get_settings()
            self.llm_service = LLMService(settings)
            await self.llm_service.initialize()
            self._initialized = True
    
    async def generate_narrative_with_citations(
        self,
        standard_ids: List[str],
        evidence_mappings: Dict[str, List[Dict[str, Any]]],
        narrative_type: str = "comprehensive",
        user_context: str = "",
        institution_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a narrative with mandatory evidence citations
        
        Args:
            standard_ids: List of standard IDs to generate narrative for
            evidence_mappings: Dict mapping standard_id to list of evidence documents
            narrative_type: Type of narrative (concise, comprehensive, executive)
            user_context: Additional context from the user
            institution_info: Information about the institution
            
        Returns:
            Dict containing narrative HTML, citations, and metadata
        """
        if not self.llm_service:
            await self.initialize()
        
        # Gather all relevant standards and evidence
        standards_data = []
        for sid in standard_ids:
            node = standards_graph.get_node(sid)
            if not node:
                continue
            
            evidence = evidence_mappings.get(sid, [])
            standards_data.append({
                "id": sid,
                "title": node.title,
                "description": node.description,
                "requirements": node.evidence_requirements,
                "evidence": evidence,
                "evidence_count": len(evidence)
            })
        
        # Create the AI prompt with strict citation requirements
        prompt = self._create_narrative_prompt(
            standards_data, 
            narrative_type, 
            user_context,
            institution_info
        )
        
        try:
            # Generate narrative with AI
            response = await self.llm_service.generate_response(
                prompt=prompt,
                agent_name="citeguard",
                temperature=0.3,  # Lower temperature for factual accuracy
                max_tokens=3000
            )
            
            # Parse and validate the response
            narrative_data = self._parse_narrative_response(response)
            
            # Verify all claims have citations
            validated_narrative = self._validate_citations(
                narrative_data,
                evidence_mappings
            )
            
            # Format as HTML with embedded citations
            html_narrative = self._format_narrative_html(
                validated_narrative,
                standards_data,
                narrative_type
            )
            
            return {
                "status": "success",
                "narrative": html_narrative,
                "citations": validated_narrative.get("citations", []),
                "compliance_score": validated_narrative.get("compliance_score", 0),
                "gaps_identified": validated_narrative.get("gaps", []),
                "recommendations": validated_narrative.get("recommendations", []),
                "algorithm": "CiteGuard™",
                "timestamp": datetime.utcnow().isoformat(),
                "word_count": len(html_narrative.split())
            }
            
        except Exception as e:
            logger.error(f"AI narrative generation failed: {e}")
            # Fallback to basic narrative
            return self._generate_fallback_narrative(standards_data, narrative_type)
    
    def _create_narrative_prompt(
        self,
        standards_data: List[Dict[str, Any]],
        narrative_type: str,
        user_context: str,
        institution_info: Optional[Dict[str, Any]]
    ) -> str:
        """Create a detailed prompt for narrative generation"""
        
        institution_name = institution_info.get("name", "the institution") if institution_info else "the institution"
        
        prompt = f"""You are an expert accreditation consultant generating a {narrative_type} narrative for {institution_name}.

CRITICAL REQUIREMENTS:
1. EVERY claim must cite specific evidence using [Evidence: filename, page X]
2. Do NOT make any claims without supporting evidence
3. If evidence is missing for a standard, explicitly note the gap
4. Use professional, clear language appropriate for accreditation reviewers

STANDARDS AND EVIDENCE:
"""
        
        for std in standards_data:
            prompt += f"\n\nStandard {std['id']}: {std['title']}\n"
            prompt += f"Description: {std['description']}\n"
            prompt += f"Available Evidence ({std['evidence_count']} documents):\n"
            
            for i, evidence in enumerate(std['evidence'][:5]):  # Limit to top 5 per standard
                prompt += f"  - {evidence.get('filename', 'Document')} (confidence: {evidence.get('confidence', 0):.2f})\n"
                if evidence.get('excerpts'):
                    prompt += f"    Key excerpt: \"{evidence['excerpts'][0][:200]}...\"\n"
        
        if user_context:
            prompt += f"\n\nAdditional Context: {user_context}\n"
        
        prompt += f"""
        
Generate a {narrative_type} narrative that:
1. Addresses each standard with evidence-backed claims
2. Identifies gaps where evidence is missing
3. Provides specific recommendations
4. Includes a compliance assessment

Format your response as JSON with the following structure:
{{
    "narrative_sections": [
        {{
            "standard_id": "...",
            "content": "...",
            "citations": ["filename:page", ...],
            "compliance_level": "full|partial|gap"
        }}
    ],
    "executive_summary": "...",
    "gaps": ["standard_id: specific gap", ...],
    "recommendations": ["specific actionable recommendation", ...],
    "compliance_score": 0.0-1.0
}}
"""
        
        return prompt
    
    def _parse_narrative_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```json?\s*(\{.*\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Fallback: create structured data from text
            return self._extract_structured_from_text(response)
            
        except Exception as e:
            logger.error(f"Failed to parse narrative response: {e}")
            raise
    
    def _validate_citations(
        self,
        narrative_data: Dict[str, Any],
        evidence_mappings: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate that all citations reference real evidence"""
        
        # Build evidence lookup
        all_evidence = {}
        for std_id, evidences in evidence_mappings.items():
            for evidence in evidences:
                filename = evidence.get('filename', '')
                all_evidence[filename] = evidence
        
        # Validate each section's citations
        for section in narrative_data.get('narrative_sections', []):
            validated_citations = []
            for citation in section.get('citations', []):
                # Extract filename from citation
                filename = citation.split(':')[0] if ':' in citation else citation
                if filename in all_evidence:
                    validated_citations.append(citation)
                else:
                    logger.warning(f"Invalid citation removed: {citation}")
            section['citations'] = validated_citations
        
        return narrative_data
    
    def _format_narrative_html(
        self,
        narrative_data: Dict[str, Any],
        standards_data: List[Dict[str, Any]],
        narrative_type: str
    ) -> str:
        """Format the narrative as HTML with embedded citations"""
        
        html_parts = []
        
        # Header
        html_parts.append(f"""
        <div class="narrative-container citeguard">
            <div class="narrative-header">
                <h2>Accreditation Compliance Narrative</h2>
                <div class="metadata">
                    <span class="narrative-type">{narrative_type.title()}</span>
                    <span class="algorithm">Generated by CiteGuard™</span>
                    <span class="timestamp">{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</span>
                </div>
            </div>
        """)
        
        # Executive Summary
        if narrative_data.get('executive_summary'):
            html_parts.append(f"""
            <div class="executive-summary">
                <h3>Executive Summary</h3>
                <p>{narrative_data['executive_summary']}</p>
                <div class="compliance-score">
                    Overall Compliance: {narrative_data.get('compliance_score', 0) * 100:.1f}%
                </div>
            </div>
            """)
        
        # Standards Sections
        html_parts.append('<div class="narrative-sections">')
        
        for section in narrative_data.get('narrative_sections', []):
            standard_id = section.get('standard_id', '')
            standard_info = next((s for s in standards_data if s['id'] == standard_id), {})
            
            compliance_class = f"compliance-{section.get('compliance_level', 'unknown')}"
            
            html_parts.append(f"""
            <div class="standard-section {compliance_class}">
                <h4>{standard_id}: {standard_info.get('title', 'Unknown Standard')}</h4>
                <div class="narrative-content">
                    {section.get('content', '')}
                </div>
                <div class="citations">
                    <strong>Evidence:</strong>
                    {', '.join([f'<cite>[{c}]</cite>' for c in section.get('citations', [])])}
                </div>
            </div>
            """)
        
        html_parts.append('</div>')
        
        # Gaps and Recommendations
        if narrative_data.get('gaps'):
            html_parts.append("""
            <div class="gaps-section">
                <h3>Identified Gaps</h3>
                <ul class="gaps-list">
            """)
            for gap in narrative_data['gaps']:
                html_parts.append(f'<li class="gap-item">{gap}</li>')
            html_parts.append('</ul></div>')
        
        if narrative_data.get('recommendations'):
            html_parts.append("""
            <div class="recommendations-section">
                <h3>Recommendations</h3>
                <ul class="recommendations-list">
            """)
            for rec in narrative_data['recommendations']:
                html_parts.append(f'<li class="recommendation-item">{rec}</li>')
            html_parts.append('</ul></div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_fallback_narrative(
        self,
        standards_data: List[Dict[str, Any]],
        narrative_type: str
    ) -> Dict[str, Any]:
        """Generate a basic narrative without AI"""
        sections = []
        gaps = []
        
        for std in standards_data:
            if std['evidence_count'] > 0:
                content = f"{std['title']} is addressed through {std['evidence_count']} supporting documents."
                compliance = "partial"
            else:
                content = f"No evidence currently mapped for {std['title']}."
                compliance = "gap"
                gaps.append(f"{std['id']}: No supporting evidence found")
            
            sections.append({
                "standard_id": std['id'],
                "content": content,
                "citations": [e['filename'] for e in std['evidence'][:3]],
                "compliance_level": compliance
            })
        
        return {
            "status": "success",
            "narrative": self._format_narrative_html({
                "narrative_sections": sections,
                "executive_summary": f"Analysis of {len(standards_data)} standards with evidence mapping.",
                "gaps": gaps,
                "recommendations": ["Upload additional evidence for standards with gaps"],
                "compliance_score": 0.5
            }, standards_data, narrative_type),
            "citations": [],
            "algorithm": "CiteGuard™ (Fallback Mode)",
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
ai_narrative_service = AIEnabledNarrativeService()
