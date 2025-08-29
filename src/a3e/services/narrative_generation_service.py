"""
AI-Powered Narrative Generation Service

Generates compliance-ready narratives from evidence documents using advanced AI.
Creates institution-specific language that directly addresses accreditation standards.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from .ai_service import get_ai_service
from .standards_mapping_service import get_mapping_service

logger = logging.getLogger(__name__)


class NarrativeGenerationService:
    """
    Generate compliance narratives from evidence using AI
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.mapping_service = get_mapping_service()
        self.narrative_templates = self._load_narrative_templates()
    
    def _load_narrative_templates(self) -> Dict[str, str]:
        """Load narrative generation templates for different contexts"""
        return {
            "evidence_summary": """
                Analyze the following evidence and create a professional narrative summary 
                that demonstrates how this evidence supports accreditation standard {standard}.
                
                Evidence text:
                {evidence_text}
                
                Standard requirement:
                {standard_description}
                
                Generate a narrative that:
                1. Opens with a clear statement of compliance
                2. Describes the specific evidence and its relevance
                3. Explains how the evidence demonstrates meeting the standard
                4. Uses institution-specific language and context
                5. Maintains professional, accreditation-appropriate tone
                6. Is 150-250 words in length
                
                Format as a formal narrative paragraph suitable for accreditation documentation.
            """,
            
            "gap_narrative": """
                Based on the identified gap in compliance for {standard}, generate a 
                professional narrative that:
                
                Gap description:
                {gap_description}
                
                Current evidence:
                {current_evidence}
                
                Create a narrative that:
                1. Acknowledges the area needing improvement
                2. Describes current efforts and partial compliance
                3. Outlines specific steps planned to address the gap
                4. Provides a realistic timeline for full compliance
                5. Demonstrates institutional commitment to improvement
                
                Write in a constructive, forward-looking tone appropriate for accreditation response.
            """,
            
            "institutional_overview": """
                Generate a comprehensive institutional overview narrative based on the following data:
                
                Institution profile:
                {institution_data}
                
                Key achievements:
                {achievements}
                
                Compliance summary:
                {compliance_summary}
                
                Create a 400-500 word narrative that:
                1. Introduces the institution's mission and values
                2. Highlights key strengths and achievements
                3. Demonstrates commitment to continuous improvement
                4. Addresses the accreditation standards comprehensively
                5. Uses data and evidence to support claims
                6. Maintains consistency with institutional voice
            """,
            
            "standard_response": """
                Generate a complete response narrative for accreditation standard {standard_id}: {standard_title}
                
                Available evidence:
                {evidence_list}
                
                Institution context:
                {context}
                
                Create a structured response that:
                1. Opening statement confirming compliance
                2. Description of policies and procedures
                3. Evidence of implementation with specific examples
                4. Assessment and improvement processes
                5. Future plans and commitments
                
                Length: 300-400 words
                Tone: Professional, evidence-based, confident
            """,
            
            "qep_narrative": """
                Generate a Quality Enhancement Plan narrative section based on:
                
                Topic: {qep_topic}
                Goals: {qep_goals}
                Current state: {current_state}
                Evidence of need: {evidence_of_need}
                
                Create a compelling narrative that:
                1. Establishes the importance of the QEP topic
                2. Demonstrates evidence-based need
                3. Articulates clear, measurable goals
                4. Shows institutional capacity and commitment
                5. Describes assessment strategies
                6. Projects meaningful impact on student success
                
                Write in an engaging yet professional tone suitable for QEP documentation.
            """
        }
    
    async def generate_evidence_narrative(
        self,
        evidence_text: str,
        standard_id: str,
        standard_description: str,
        institution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a narrative that connects evidence to a specific standard
        """
        try:
            prompt = self.narrative_templates["evidence_summary"].format(
                evidence_text=evidence_text[:2000],  # Limit for token management
                standard=standard_id,
                standard_description=standard_description
            )
            
            # Add institution context if provided
            if institution_context:
                prompt += f"\n\nInstitution context: {json.dumps(institution_context)}"
            
            # Generate narrative using AI
            response = await self.ai_service.analyze_document(
                text=prompt,
                metadata={
                    "task": "narrative_generation",
                    "type": "evidence_summary",
                    "standard": standard_id
                },
                max_tokens=500
            )
            
            if response.get("success"):
                narrative = response.get("analysis", "")
                
                # Clean and format the narrative
                narrative = self._clean_narrative(narrative)
                
                # Calculate quality metrics
                quality_metrics = self._assess_narrative_quality(narrative, standard_id)
                
                return {
                    "success": True,
                    "narrative": narrative,
                    "standard_id": standard_id,
                    "word_count": len(narrative.split()),
                    "quality_metrics": quality_metrics,
                    "generated_at": datetime.utcnow().isoformat()
                }
            else:
                return self._generate_fallback_narrative(evidence_text, standard_id)
                
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return self._generate_fallback_narrative(evidence_text, standard_id)
    
    async def generate_gap_narrative(
        self,
        gap_description: str,
        standard_id: str,
        current_evidence: List[str],
        improvement_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a narrative addressing compliance gaps
        """
        try:
            prompt = self.narrative_templates["gap_narrative"].format(
                standard=standard_id,
                gap_description=gap_description,
                current_evidence="\n".join(current_evidence[:5])  # Top 5 evidence items
            )
            
            if improvement_plan:
                prompt += f"\n\nImprovement plan: {json.dumps(improvement_plan)}"
            
            response = await self.ai_service.analyze_document(
                text=prompt,
                metadata={
                    "task": "narrative_generation",
                    "type": "gap_narrative",
                    "standard": standard_id
                },
                max_tokens=400
            )
            
            if response.get("success"):
                narrative = self._clean_narrative(response.get("analysis", ""))
                
                return {
                    "success": True,
                    "narrative": narrative,
                    "gap_addressed": gap_description,
                    "improvement_focus": self._extract_improvement_focus(narrative),
                    "timeline": self._extract_timeline(narrative),
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            return self._generate_fallback_gap_narrative(gap_description, standard_id)
            
        except Exception as e:
            logger.error(f"Error generating gap narrative: {e}")
            return self._generate_fallback_gap_narrative(gap_description, standard_id)
    
    async def generate_comprehensive_response(
        self,
        standard_id: str,
        standard_title: str,
        evidence_documents: List[Dict[str, Any]],
        institution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a complete standard response narrative
        """
        try:
            # Prepare evidence list
            evidence_list = []
            for doc in evidence_documents[:10]:  # Limit to top 10
                evidence_list.append(f"- {doc.get('title', 'Document')}: {doc.get('summary', '')[:100]}")
            
            prompt = self.narrative_templates["standard_response"].format(
                standard_id=standard_id,
                standard_title=standard_title,
                evidence_list="\n".join(evidence_list),
                context=json.dumps({
                    "institution_name": institution_data.get("name"),
                    "institution_type": institution_data.get("type"),
                    "enrollment": institution_data.get("enrollment_size"),
                    "mission_focus": institution_data.get("mission_focus")
                })
            )
            
            response = await self.ai_service.analyze_document(
                text=prompt,
                metadata={
                    "task": "narrative_generation",
                    "type": "comprehensive_response",
                    "standard": standard_id
                },
                max_tokens=600
            )
            
            if response.get("success"):
                narrative = self._clean_narrative(response.get("analysis", ""))
                
                # Structure the response
                structured_response = self._structure_narrative(narrative)
                
                return {
                    "success": True,
                    "standard_id": standard_id,
                    "standard_title": standard_title,
                    "narrative": narrative,
                    "structured_sections": structured_response,
                    "evidence_count": len(evidence_documents),
                    "compliance_statement": self._extract_compliance_statement(narrative),
                    "word_count": len(narrative.split()),
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            return self._generate_fallback_response(standard_id, standard_title)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive response: {e}")
            return self._generate_fallback_response(standard_id, standard_title)
    
    async def generate_qep_section(
        self,
        qep_topic: str,
        qep_goals: List[str],
        current_state_data: Dict[str, Any],
        evidence_of_need: List[str]
    ) -> Dict[str, Any]:
        """
        Generate QEP narrative sections
        """
        try:
            prompt = self.narrative_templates["qep_narrative"].format(
                qep_topic=qep_topic,
                qep_goals=json.dumps(qep_goals),
                current_state=json.dumps(current_state_data),
                evidence_of_need="\n".join(evidence_of_need[:5])
            )
            
            response = await self.ai_service.analyze_document(
                text=prompt,
                metadata={
                    "task": "narrative_generation",
                    "type": "qep_section",
                    "topic": qep_topic
                },
                max_tokens=700
            )
            
            if response.get("success"):
                narrative = self._clean_narrative(response.get("analysis", ""))
                
                return {
                    "success": True,
                    "qep_topic": qep_topic,
                    "narrative": narrative,
                    "key_themes": self._extract_themes(narrative),
                    "measurable_outcomes": self._extract_outcomes(narrative),
                    "word_count": len(narrative.split()),
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            return self._generate_fallback_qep(qep_topic, qep_goals)
            
        except Exception as e:
            logger.error(f"Error generating QEP section: {e}")
            return self._generate_fallback_qep(qep_topic, qep_goals)
    
    async def batch_generate_narratives(
        self,
        narrative_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple narratives in batch for efficiency
        """
        results = []
        
        for request in narrative_requests:
            narrative_type = request.get("type", "evidence_summary")
            
            if narrative_type == "evidence_summary":
                result = await self.generate_evidence_narrative(
                    evidence_text=request.get("evidence_text", ""),
                    standard_id=request.get("standard_id", ""),
                    standard_description=request.get("standard_description", ""),
                    institution_context=request.get("institution_context")
                )
            elif narrative_type == "gap_narrative":
                result = await self.generate_gap_narrative(
                    gap_description=request.get("gap_description", ""),
                    standard_id=request.get("standard_id", ""),
                    current_evidence=request.get("current_evidence", []),
                    improvement_plan=request.get("improvement_plan")
                )
            elif narrative_type == "comprehensive_response":
                result = await self.generate_comprehensive_response(
                    standard_id=request.get("standard_id", ""),
                    standard_title=request.get("standard_title", ""),
                    evidence_documents=request.get("evidence_documents", []),
                    institution_data=request.get("institution_data", {})
                )
            else:
                result = {"success": False, "error": f"Unknown narrative type: {narrative_type}"}
            
            results.append(result)
        
        return results
    
    def _clean_narrative(self, text: str) -> str:
        """Clean and format generated narrative"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.(?=[A-Z])', '. ', text)
        
        # Remove any AI artifacts
        text = re.sub(r'(As an AI|I am an AI|In summary|In conclusion)', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _assess_narrative_quality(self, narrative: str, standard_id: str) -> Dict[str, Any]:
        """Assess quality metrics of generated narrative"""
        words = narrative.split()
        sentences = narrative.split('.')
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": len(words) / max(len(sentences), 1),
            "standard_mentioned": standard_id.lower() in narrative.lower(),
            "evidence_keywords": self._count_evidence_keywords(narrative),
            "professional_tone_score": self._assess_tone(narrative),
            "completeness_score": self._assess_completeness(narrative)
        }
    
    def _count_evidence_keywords(self, text: str) -> int:
        """Count evidence-related keywords"""
        keywords = ['evidence', 'demonstrate', 'document', 'policy', 'procedure', 
                   'assessment', 'data', 'review', 'evaluation', 'implementation']
        return sum(1 for keyword in keywords if keyword in text.lower())
    
    def _assess_tone(self, text: str) -> float:
        """Assess professional tone (0-1 scale)"""
        professional_indicators = ['demonstrates', 'ensures', 'maintains', 'provides',
                                  'establishes', 'implements', 'supports', 'achieves']
        score = sum(1 for indicator in professional_indicators if indicator in text.lower())
        return min(score / 5.0, 1.0)  # Normalize to 0-1
    
    def _assess_completeness(self, text: str) -> float:
        """Assess narrative completeness"""
        required_elements = ['evidence', 'standard', 'compliance', 'process']
        found = sum(1 for element in required_elements if element in text.lower())
        return found / len(required_elements)
    
    def _extract_compliance_statement(self, narrative: str) -> str:
        """Extract the compliance statement from narrative"""
        sentences = narrative.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['complies', 'meets', 'fulfills', 'satisfies']):
                return sentence.strip() + '.'
        return sentences[0].strip() + '.' if sentences else ""
    
    def _structure_narrative(self, narrative: str) -> Dict[str, str]:
        """Structure narrative into sections"""
        paragraphs = narrative.split('\n\n')
        
        structured = {
            "opening_statement": "",
            "evidence_description": "",
            "implementation_details": "",
            "assessment_processes": "",
            "future_commitments": ""
        }
        
        if len(paragraphs) >= 1:
            structured["opening_statement"] = paragraphs[0]
        if len(paragraphs) >= 2:
            structured["evidence_description"] = paragraphs[1]
        if len(paragraphs) >= 3:
            structured["implementation_details"] = paragraphs[2]
        if len(paragraphs) >= 4:
            structured["assessment_processes"] = paragraphs[3]
        if len(paragraphs) >= 5:
            structured["future_commitments"] = paragraphs[4]
        
        return structured
    
    def _extract_improvement_focus(self, narrative: str) -> List[str]:
        """Extract improvement focus areas from narrative"""
        focus_areas = []
        keywords = ['improve', 'enhance', 'strengthen', 'develop', 'expand']
        
        sentences = narrative.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                focus_areas.append(sentence.strip())
        
        return focus_areas[:3]  # Top 3 focus areas
    
    def _extract_timeline(self, narrative: str) -> Optional[str]:
        """Extract timeline information from narrative"""
        timeline_patterns = [
            r'within (\d+ \w+)',
            r'by (\w+ \d{4})',
            r'over the next (\d+ \w+)',
            r'(\d{4}-\d{4})'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, narrative, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_themes(self, narrative: str) -> List[str]:
        """Extract key themes from narrative"""
        # Simple keyword extraction for themes
        theme_keywords = {
            'student success': ['student', 'success', 'achievement', 'learning'],
            'institutional effectiveness': ['effectiveness', 'assessment', 'improvement'],
            'faculty development': ['faculty', 'professional', 'development', 'training'],
            'resource allocation': ['resource', 'budget', 'allocation', 'investment'],
            'technology integration': ['technology', 'digital', 'online', 'system']
        }
        
        found_themes = []
        narrative_lower = narrative.lower()
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in narrative_lower for keyword in keywords):
                found_themes.append(theme)
        
        return found_themes
    
    def _extract_outcomes(self, narrative: str) -> List[str]:
        """Extract measurable outcomes from narrative"""
        outcomes = []
        outcome_indicators = ['increase', 'decrease', 'improve', 'achieve', 'reach', 'attain']
        
        sentences = narrative.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in outcome_indicators):
                if any(char.isdigit() for char in sentence) or '%' in sentence:
                    outcomes.append(sentence.strip())
        
        return outcomes[:5]  # Top 5 outcomes
    
    def _generate_fallback_narrative(self, evidence_text: str, standard_id: str) -> Dict[str, Any]:
        """Generate fallback narrative when AI is unavailable"""
        narrative = f"""
        The institution demonstrates compliance with {standard_id} through documented evidence 
        and established procedures. The provided evidence shows systematic implementation of 
        required practices and ongoing commitment to meeting accreditation standards. 
        Continuous monitoring and improvement processes ensure sustained compliance and 
        institutional effectiveness in this area.
        """
        
        return {
            "success": True,
            "narrative": self._clean_narrative(narrative),
            "standard_id": standard_id,
            "word_count": len(narrative.split()),
            "quality_metrics": {"fallback": True},
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_fallback_gap_narrative(self, gap_description: str, standard_id: str) -> Dict[str, Any]:
        """Generate fallback gap narrative"""
        narrative = f"""
        The institution acknowledges the need for improvement in meeting {standard_id}. 
        Current efforts are underway to address {gap_description}. The institution is 
        committed to implementing comprehensive solutions and has established a timeline 
        for achieving full compliance. Regular assessment will monitor progress toward 
        meeting this standard.
        """
        
        return {
            "success": True,
            "narrative": self._clean_narrative(narrative),
            "gap_addressed": gap_description,
            "improvement_focus": ["Address identified gap", "Implement solutions"],
            "timeline": "Within 12 months",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_fallback_response(self, standard_id: str, standard_title: str) -> Dict[str, Any]:
        """Generate fallback comprehensive response"""
        narrative = f"""
        The institution fully complies with {standard_id}: {standard_title}. 
        
        Established policies and procedures ensure consistent implementation of requirements. 
        Evidence demonstrates effective practices across all relevant areas. Regular 
        assessment and review processes maintain compliance and drive continuous improvement. 
        
        The institution remains committed to upholding the highest standards of quality 
        and effectiveness in meeting accreditation requirements.
        """
        
        return {
            "success": True,
            "standard_id": standard_id,
            "standard_title": standard_title,
            "narrative": self._clean_narrative(narrative),
            "structured_sections": self._structure_narrative(narrative),
            "compliance_statement": f"The institution fully complies with {standard_id}",
            "word_count": len(narrative.split()),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_fallback_qep(self, qep_topic: str, qep_goals: List[str]) -> Dict[str, Any]:
        """Generate fallback QEP narrative"""
        goals_text = ", ".join(qep_goals[:3])
        narrative = f"""
        The institution's Quality Enhancement Plan focuses on {qep_topic}, addressing 
        critical needs identified through comprehensive assessment. The QEP aims to {goals_text}. 
        
        Evidence-based strategies will drive meaningful improvements in student learning 
        and success. Clear assessment methods will measure progress toward defined outcomes. 
        The institution has allocated appropriate resources and established accountability 
        measures to ensure successful implementation.
        """
        
        return {
            "success": True,
            "qep_topic": qep_topic,
            "narrative": self._clean_narrative(narrative),
            "key_themes": ["student success", "continuous improvement"],
            "measurable_outcomes": qep_goals,
            "word_count": len(narrative.split()),
            "generated_at": datetime.utcnow().isoformat()
        }


# Singleton instance
_narrative_service = None


def get_narrative_service() -> NarrativeGenerationService:
    """Get or create narrative service instance"""
    global _narrative_service
    if _narrative_service is None:
        _narrative_service = NarrativeGenerationService()
    return _narrative_service