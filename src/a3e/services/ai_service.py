"""
Enhanced AI Service with Multi-Provider Support

Provides AI capabilities using Anthropic (primary) and OpenAI (fallback),
ensuring maximum reliability for document processing and analysis.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import AI providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available - install anthropic package")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - install openai package")


class AIProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    NONE = "none"


class AIService:
    """Multi-provider AI service with automatic failover"""
    
    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        self.primary_provider = AIProvider.NONE
        self.fallback_provider = AIProvider.NONE
        
        # Try to initialize Anthropic (preferred)
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPICAI_API_KEY')
        if ANTHROPIC_AVAILABLE and anthropic_key:
            try:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_key)
                self.primary_provider = AIProvider.ANTHROPIC
                logger.info("✅ Anthropic AI initialized as primary provider")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        # Try to initialize OpenAI (fallback)
        openai_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if OPENAI_AVAILABLE and openai_key:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
                if self.primary_provider == AIProvider.NONE:
                    self.primary_provider = AIProvider.OPENAI
                    logger.info("✅ OpenAI initialized as primary provider")
                else:
                    self.fallback_provider = AIProvider.OPENAI
                    logger.info("✅ OpenAI initialized as fallback provider")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        if self.primary_provider == AIProvider.NONE:
            logger.warning("⚠️ No AI provider available - using basic processing")
    
    async def analyze_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Analyze document content using available AI provider
        
        Args:
            text: Document text to analyze
            metadata: Document metadata
            max_tokens: Maximum response tokens
            
        Returns:
            Analysis results with fallback to basic analysis if needed
        """
        
        # Try primary provider
        if self.primary_provider == AIProvider.ANTHROPIC:
            result = await self._analyze_with_anthropic(text, metadata, max_tokens)
            if result:
                return result
            # Fall back to OpenAI if Anthropic fails
            if self.fallback_provider == AIProvider.OPENAI:
                logger.info("Falling back to OpenAI...")
                result = await self._analyze_with_openai(text, metadata, max_tokens)
                if result:
                    return result
        
        elif self.primary_provider == AIProvider.OPENAI:
            result = await self._analyze_with_openai(text, metadata, max_tokens)
            if result:
                return result
        
        # Final fallback to basic analysis
        return self._basic_analysis(text, metadata)
    
    async def _analyze_with_anthropic(
        self,
        text: str,
        metadata: Dict[str, Any],
        max_tokens: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze using Anthropic Claude"""
        
        if not self.anthropic_client:
            return None
        
        try:
            prompt = self._build_analysis_prompt(text, metadata)
            
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective
                max_tokens=max_tokens,
                temperature=0.3,
                system="You are an expert accreditation analyst specializing in higher education compliance. Analyze documents for evidence mapping to accreditation standards. Always respond with valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text if response.content else "{}"
            analysis = json.loads(content)
            analysis['ai_provider'] = 'anthropic'
            analysis['ai_model'] = 'claude-3-haiku'
            
            logger.info("✅ Document analyzed with Anthropic")
            return analysis
            
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            return None
    
    async def _analyze_with_openai(
        self,
        text: str,
        metadata: Dict[str, Any],
        max_tokens: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze using OpenAI GPT"""
        
        if not self.openai_client:
            return None
        
        try:
            prompt = self._build_analysis_prompt(text, metadata)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Affordable and capable
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert accreditation analyst specializing in higher education compliance. Analyze documents for evidence mapping to accreditation standards."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=max_tokens
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis['ai_provider'] = 'openai'
            analysis['ai_model'] = 'gpt-4o-mini'
            
            logger.info("✅ Document analyzed with OpenAI")
            return analysis
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    def _build_analysis_prompt(self, text: str, metadata: Dict[str, Any]) -> str:
        """Build the analysis prompt for AI providers"""
        
        return f"""Analyze this academic document for accreditation evidence.
        
Document: {metadata.get('filename', 'Unknown')}
Institution: {metadata.get('institution_name', 'Unknown')}
Accreditor: {metadata.get('accreditor', 'SACSCOC')}

Document Text (first 3000 chars):
{text[:3000]}

Provide a JSON response with:
1. document_type: Type of document (e.g., "strategic_plan", "assessment_report", "policy", etc.)
2. key_topics: List of 5-10 main topics covered
3. evidence_elements: List of specific evidence items relevant to accreditation
4. compliance_areas: List of compliance areas addressed
5. strengths: List of institutional strengths demonstrated
6. potential_gaps: Any potential compliance gaps or areas needing attention
7. recommendations: Specific recommendations for using this evidence
8. confidence_score: 0-100 score for how relevant this is to accreditation"""
    
    def _basic_analysis(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Basic keyword-based analysis when AI is not available"""
        
        keywords = {
            'strategic_planning': ['strategic', 'plan', 'mission', 'vision', 'goals'],
            'assessment': ['assessment', 'learning outcomes', 'evaluation', 'rubric'],
            'governance': ['board', 'governance', 'policy', 'administration'],
            'faculty': ['faculty', 'professor', 'instructor', 'qualification'],
            'student_services': ['student', 'support', 'services', 'advising'],
            'finance': ['budget', 'financial', 'audit', 'revenue'],
            'facilities': ['facilities', 'campus', 'infrastructure', 'safety'],
            'technology': ['technology', 'IT', 'digital', 'online']
        }
        
        text_lower = text.lower()
        detected_areas = []
        
        for area, terms in keywords.items():
            if any(term in text_lower for term in terms):
                detected_areas.append(area)
        
        return {
            'document_type': 'general',
            'key_topics': detected_areas[:5],
            'evidence_elements': [f"Evidence related to {area}" for area in detected_areas[:3]],
            'compliance_areas': detected_areas,
            'strengths': ["Document provides evidence"],
            'potential_gaps': ["AI analysis unavailable - manual review recommended"],
            'recommendations': ["Review document for specific standard mapping"],
            'confidence_score': 40,
            'ai_provider': 'none',
            'analysis_method': 'keyword_matching'
        }
    
    async def map_to_standards(
        self,
        text: str,
        analysis: Dict[str, Any],
        standards: List[Dict[str, Any]],
        accreditor: str = "SACSCOC"
    ) -> List[Dict[str, Any]]:
        """
        Map document to specific accreditation standards
        
        Args:
            text: Document text
            analysis: Document analysis results
            standards: List of available standards
            accreditor: Accreditor name
            
        Returns:
            List of standard mappings
        """
        
        if not standards:
            return []
        
        # Try AI mapping first
        if self.primary_provider != AIProvider.NONE:
            mappings = await self._ai_standard_mapping(analysis, standards, accreditor)
            if mappings:
                return mappings
        
        # Fallback to basic mapping
        return self._basic_standard_mapping(analysis, standards)
    
    async def _ai_standard_mapping(
        self,
        analysis: Dict[str, Any],
        standards: List[Dict[str, Any]],
        accreditor: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Use AI to map document to standards"""
        
        prompt = f"""Map this document analysis to specific {accreditor} standards.

Analysis Summary:
- Document Type: {analysis.get('document_type', 'Unknown')}
- Key Topics: {', '.join(analysis.get('key_topics', []))}
- Evidence Elements: {', '.join(analysis.get('evidence_elements', [])[:5])}

Available Standards (sample):
{json.dumps(standards[:10], indent=2)}

Return a JSON array of mappings, each with:
- standard_id: The standard identifier
- standard_title: The standard title
- relevance_score: 0-100 how relevant the evidence is
- evidence_summary: Brief description of how document addresses this standard
- mapping_confidence: "high", "medium", or "low"
"""
        
        try:
            if self.primary_provider == AIProvider.ANTHROPIC:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.2,
                    system=f"You are an expert in {accreditor} accreditation standards. Map evidence to specific standards accurately. Return only valid JSON.",
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text if response.content else "[]"
                
            elif self.primary_provider == AIProvider.OPENAI:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are an expert in {accreditor} accreditation standards."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1000
                )
                content = response.choices[0].message.content
            else:
                return None
            
            result = json.loads(content)
            mappings = result.get('mappings', []) if 'mappings' in result else result if isinstance(result, list) else []
            return mappings
            
        except Exception as e:
            logger.error(f"AI standard mapping failed: {e}")
            return None
    
    def _basic_standard_mapping(
        self,
        analysis: Dict[str, Any],
        standards: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Basic standard mapping without AI"""
        
        mappings = []
        compliance_areas = analysis.get('compliance_areas', [])
        
        for standard in standards[:5]:  # Map to first 5 standards as demo
            if any(area in standard.get('title', '').lower() for area in compliance_areas):
                mappings.append({
                    'standard_id': standard.get('id', 'unknown'),
                    'standard_title': standard.get('title', 'Unknown Standard'),
                    'relevance_score': 50,
                    'evidence_summary': 'Document contains relevant evidence for this standard',
                    'mapping_confidence': 'low'
                })
        
        return mappings
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        
        return {
            'primary_provider': self.primary_provider.value,
            'fallback_provider': self.fallback_provider.value,
            'anthropic_available': self.anthropic_client is not None,
            'openai_available': self.openai_client is not None,
            'ai_enabled': self.primary_provider != AIProvider.NONE
        }


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service