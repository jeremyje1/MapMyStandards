"""
Enhanced Evidence Mapper with LLM Integration
Combines TF-IDF retrieval with LLM-powered analysis for better mapping accuracy
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .evidence_mapper import EvidenceMapper, EvidenceDocument, MappingResult
from .llm_service import LLMService
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class EnhancedEvidenceMapper(EvidenceMapper):
    """Enhanced evidence mapper that uses LLM for intelligent analysis"""
    
    def __init__(self):
        super().__init__()
        self.llm_service = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize LLM service"""
        if not self._initialized:
            settings = get_settings()
            self.llm_service = LLMService(settings)
            await self.llm_service.initialize()
            self._initialized = True
    
    async def map_evidence_with_ai(
        self, 
        document: EvidenceDocument,
        num_candidates: int = 20,
        final_top_k: int = 10,
        use_llm: bool = True
    ) -> List[MappingResult]:
        """
        Map evidence to standards using AI-enhanced analysis
        
        Args:
            document: Evidence document to map
            num_candidates: Number of candidates from initial retrieval
            final_top_k: Number of final results to return
            use_llm: Whether to use LLM for enhanced analysis
            
        Returns:
            List of mapping results with AI-enhanced confidence and explanations
        """
        # First, use traditional TF-IDF mapping to get candidates
        initial_mappings = self.map_evidence(document, num_candidates)
        
        if not use_llm or not self.llm_service:
            return initial_mappings[:final_top_k]
        
        # Enhance mappings with LLM analysis
        enhanced_mappings = []
        
        # Process in batches for efficiency
        batch_size = 5
        for i in range(0, min(len(initial_mappings), num_candidates), batch_size):
            batch = initial_mappings[i:i+batch_size]
            
            # Prepare prompt for LLM
            prompt = self._create_mapping_prompt(document, batch)
            
            try:
                # Get LLM analysis
                response = await self.llm_service.generate_response(
                    prompt=prompt,
                    agent_name="evidence_mapper",
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=1500
                )
                
                # Parse LLM response
                enhanced_results = self._parse_llm_response(response.content, batch)
                enhanced_mappings.extend(enhanced_results)
                
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to TF-IDF: {e}")
                enhanced_mappings.extend(batch)
        
        # Sort by AI-enhanced confidence
        enhanced_mappings.sort(key=lambda x: x.confidence, reverse=True)
        
        return enhanced_mappings[:final_top_k]
    
    def _create_mapping_prompt(self, document: EvidenceDocument, mappings: List[MappingResult]) -> str:
        """Create prompt for LLM to analyze evidence-standard mappings"""
        
        # Truncate document text if too long
        max_doc_length = 2000
        doc_text = document.text[:max_doc_length] + "..." if len(document.text) > max_doc_length else document.text
        
        prompt = f"""You are an expert accreditation analyst. Analyze how well the following evidence document maps to accreditation standards.

EVIDENCE DOCUMENT:
Title: {document.doc_id}
Content: {doc_text}

CANDIDATE STANDARDS TO EVALUATE:
"""
        
        for i, mapping in enumerate(mappings, 1):
            prompt += f"""
{i}. Standard ID: {mapping.standard_id}
   Title: {mapping.standard_title}
   Accreditor: {mapping.accreditor}
   Initial Confidence: {mapping.confidence:.2f}
"""
        
        prompt += """

For each standard, provide:
1. A confidence score (0.0-1.0) based on how well the evidence addresses the standard
2. Specific text spans from the evidence that support the mapping (max 3)
3. A brief explanation of why this evidence does or doesn't meet the standard
4. Match type: 'exact' (directly addresses all requirements), 'strong' (addresses most requirements), 'partial' (addresses some requirements), 'weak' (tangentially related)

Format your response as JSON:
{
  "mappings": [
    {
      "standard_id": "...",
      "confidence": 0.XX,
      "match_type": "exact|strong|partial|weak",
      "rationale_spans": ["specific quote 1", "specific quote 2"],
      "explanation": "This evidence demonstrates... because..."
    }
  ]
}

Focus on accuracy and compliance requirements. Be conservative with confidence scores."""
        
        return prompt
    
    def _parse_llm_response(self, response: str, original_mappings: List[MappingResult]) -> List[MappingResult]:
        """Parse LLM response and create enhanced mapping results"""
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Create mapping lookup
            mapping_dict = {m.standard_id: m for m in original_mappings}
            
            enhanced_mappings = []
            for item in data.get('mappings', []):
                standard_id = item.get('standard_id')
                if standard_id in mapping_dict:
                    original = mapping_dict[standard_id]
                    
                    # Create enhanced mapping
                    enhanced = MappingResult(
                        standard_id=original.standard_id,
                        confidence=float(item.get('confidence', original.confidence)),
                        rationale_spans=item.get('rationale_spans', original.rationale_spans)[:3],
                        explanation=item.get('explanation', original.explanation),
                        accreditor=original.accreditor,
                        standard_title=original.standard_title,
                        match_type=item.get('match_type', original.match_type)
                    )
                    enhanced_mappings.append(enhanced)
            
            # Add any missing mappings from original
            enhanced_ids = {m.standard_id for m in enhanced_mappings}
            for original in original_mappings:
                if original.standard_id not in enhanced_ids:
                    enhanced_mappings.append(original)
            
            return enhanced_mappings
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Return original mappings if parsing fails
            return original_mappings


# Create singleton instance
enhanced_evidence_mapper = EnhancedEvidenceMapper()
