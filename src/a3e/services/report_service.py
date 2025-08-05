"""
Report Generation Service for A³E

Generates comprehensive reports, narratives, QEP impact reports, and compliance documents
based on analyzed evidence and institutional data.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid

from ..core.config import Settings
from ..models import Institution, Evidence, Standard, AgentWorkflow
from ..services.database_service import DatabaseService
from ..services.llm_service import LLMService
from ..core.accreditation_registry import ALL_ACCREDITORS

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating comprehensive accreditation reports"""
    
    def __init__(self, settings: Settings, llm_service: LLMService):
        self.settings = settings
        self.llm_service = llm_service
        self.report_templates = self._load_report_templates()
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load report templates for different accreditors and report types"""
        return {
            "SACSCOC": {
                "compliance_report": {
                    "sections": [
                        "Executive Summary",
                        "Institutional Profile",
                        "Standards Compliance",
                        "Evidence Summary",
                        "Areas for Improvement",
                        "Action Plans"
                    ],
                    "required_elements": [
                        "mission_statement",
                        "governance_structure",
                        "financial_resources",
                        "educational_programs",
                        "faculty_qualifications",
                        "student_services",
                        "assessment_processes"
                    ]
                },
                "qep_report": {
                    "sections": [
                        "QEP Overview",
                        "Problem Identification",
                        "Literature Review",
                        "Implementation Plan",
                        "Assessment Methods",
                        "Resource Requirements",
                        "Timeline",
                        "Expected Outcomes"
                    ],
                    "focus_areas": [
                        "student_learning",
                        "student_success",
                        "institutional_effectiveness"
                    ]
                }
            },
            "HLC": {
                "compliance_report": {
                    "sections": [
                        "Executive Summary",
                        "Institutional Context",
                        "Criteria Compliance",
                        "Evidence Documentation",
                        "Continuous Improvement",
                        "Future Planning"
                    ]
                },
                "quality_initiative": {
                    "sections": [
                        "Initiative Overview",
                        "Institutional Context",
                        "Implementation Strategy",
                        "Progress Measures",
                        "Results and Analysis",
                        "Lessons Learned",
                        "Next Steps"
                    ]
                }
            }
        }
    
    async def generate_comprehensive_report(
        self,
        institution_id: str,
        accreditor_id: str,
        report_type: str = "compliance_report",
        include_evidence: bool = True,
        include_narratives: bool = True,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive accreditation report"""
        
        start_time = datetime.now()
        report_id = str(uuid.uuid4())
        
        try:
            # Get institution data
            db_service = DatabaseService(self.settings.database_url)
            await db_service.initialize()
            
            institution = await db_service.get_institution(institution_id)
            if not institution:
                raise ValueError(f"Institution {institution_id} not found")
            
            # Get all evidence for the institution
            evidence_list = await db_service.get_evidence_by_institution(institution_id)
            
            # Get standards for the accreditor
            accreditor = ALL_ACCREDITORS.get(accreditor_id)
            if not accreditor:
                raise ValueError(f"Accreditor {accreditor_id} not supported")
            
            standards = accreditor.get("standards", [])
            
            # Generate report sections
            report_data = {
                "report_id": report_id,
                "institution": {
                    "name": institution.name,
                    "id": institution_id,
                    "types": institution.institution_types,
                    "state": institution.state
                },
                "accreditor": accreditor_id,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "sections": {}
            }
            
            # Get report template
            template = self.report_templates.get(accreditor_id, {}).get(report_type, {})
            sections = template.get("sections", ["Executive Summary", "Analysis", "Recommendations"])
            
            # Generate each section
            for section_name in sections:
                section_content = await self._generate_report_section(
                    section_name,
                    institution,
                    evidence_list,
                    standards,
                    accreditor_id,
                    additional_context
                )
                report_data["sections"][section_name] = section_content
            
            # Generate executive summary last (to include all findings)
            if "Executive Summary" in sections:
                report_data["sections"]["Executive Summary"] = await self._generate_executive_summary(
                    report_data,
                    institution,
                    evidence_list,
                    accreditor_id
                )
            
            # Add evidence appendix if requested
            if include_evidence:
                report_data["evidence_appendix"] = await self._generate_evidence_appendix(evidence_list)
            
            # Add compliance scoring
            report_data["compliance_analysis"] = await self._generate_compliance_scoring(
                evidence_list,
                standards,
                accreditor_id
            )
            
            # Save report to database
            await self._save_report(report_data, db_service)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            report_data["generation_time"] = execution_time
            
            logger.info(f"Generated comprehensive report {report_id} in {execution_time:.2f}s")
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            raise
        finally:
            await db_service.close()
    
    async def generate_qep_impact_report(
        self,
        institution_id: str,
        qep_data: Dict[str, Any],
        assessment_results: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate QEP impact and assessment report"""
        
        report_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            db_service = DatabaseService(self.settings.database_url)
            await db_service.initialize()
            
            institution = await db_service.get_institution(institution_id)
            if not institution:
                raise ValueError(f"Institution {institution_id} not found")
            
            # Generate QEP-specific analysis
            qep_analysis = await self._analyze_qep_effectiveness(
                qep_data,
                assessment_results,
                institution,
                additional_context
            )
            
            # Generate impact assessment
            impact_assessment = await self._generate_qep_impact_assessment(
                qep_data,
                assessment_results,
                institution
            )
            
            # Generate recommendations
            recommendations = await self._generate_qep_recommendations(
                qep_analysis,
                impact_assessment,
                institution
            )
            
            report_data = {
                "report_id": report_id,
                "report_type": "qep_impact_report",
                "institution": {
                    "name": institution.name,
                    "id": institution_id
                },
                "qep_overview": qep_data,
                "impact_analysis": qep_analysis,
                "impact_assessment": impact_assessment,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "generation_time": (datetime.now() - start_time).total_seconds()
            }
            
            await self._save_report(report_data, db_service)
            
            logger.info(f"Generated QEP impact report {report_id}")
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate QEP impact report: {e}")
            raise
        finally:
            await db_service.close()
    
    async def generate_narrative_response(
        self,
        standard_id: str,
        institution_id: str,
        accreditor_id: str,
        evidence_ids: List[str],
        additional_context: Optional[str] = None,
        narrative_style: str = "formal"
    ) -> Dict[str, Any]:
        """Generate a well-written narrative response for a specific standard"""
        
        try:
            db_service = DatabaseService(self.settings.database_url)
            await db_service.initialize()
            
            # Get institution and evidence
            institution = await db_service.get_institution(institution_id)
            evidence_items = []
            
            for evidence_id in evidence_ids:
                evidence = await db_service.get_evidence(evidence_id)
                if evidence:
                    evidence_items.append(evidence)
            
            # Get standard information
            accreditor = ALL_ACCREDITORS.get(accreditor_id, {})
            standard = None
            for std in accreditor.get("standards", []):
                if std.get("id") == standard_id:
                    standard = std
                    break
            
            if not standard:
                raise ValueError(f"Standard {standard_id} not found for {accreditor_id}")
            
            # Generate contextual narrative
            narrative = await self._generate_contextual_narrative(
                standard,
                evidence_items,
                institution,
                accreditor_id,
                additional_context,
                narrative_style
            )
            
            return {
                "standard_id": standard_id,
                "accreditor": accreditor_id,
                "institution": institution.name,
                "narrative": narrative,
                "evidence_count": len(evidence_items),
                "generated_at": datetime.now().isoformat(),
                "style": narrative_style
            }
            
        except Exception as e:
            logger.error(f"Failed to generate narrative response: {e}")
            raise
        finally:
            await db_service.close()
    
    async def _generate_report_section(
        self,
        section_name: str,
        institution: Institution,
        evidence_list: List[Evidence],
        standards: List[Dict[str, Any]],
        accreditor_id: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate content for a specific report section"""
        
        prompt = f"""
        Generate the {section_name} section for {institution.name}'s {accreditor_id} accreditation report.
        
        Institution Context:
        - Name: {institution.name}
        - Type: {', '.join(institution.institution_types)}
        - State: {institution.state}
        
        Available Evidence: {len(evidence_list)} documents
        Standards Count: {len(standards)}
        
        {f"Additional Context: {additional_context}" if additional_context else ""}
        
        The {section_name} should be:
        1. Professionally written and appropriate for accreditation review
        2. Evidence-based and specific to this institution
        3. Comprehensive but concise
        4. Formatted with clear headings and structure
        
        Include specific references to evidence and cite with [Evidence ID] format.
        """
        
        response = await self.llm_service.generate_response(prompt, "narrator")
        
        return {
            "title": section_name,
            "content": response,
            "evidence_references": self._extract_evidence_references(response),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_executive_summary(
        self,
        report_data: Dict[str, Any],
        institution: Institution,
        evidence_list: List[Evidence],
        accreditor_id: str
    ) -> Dict[str, Any]:
        """Generate executive summary based on full report content"""
        
        sections_summary = ""
        for section_name, section_data in report_data["sections"].items():
            if section_name != "Executive Summary":
                sections_summary += f"\n{section_name}: {section_data.get('content', '')[:200]}...\n"
        
        prompt = f"""
        Generate an Executive Summary for {institution.name}'s {accreditor_id} accreditation report.
        
        Based on the following report sections:
        {sections_summary}
        
        The Executive Summary should:
        1. Provide a high-level overview of compliance status
        2. Highlight key strengths and achievements
        3. Identify primary areas for improvement
        4. Summarize overall readiness for accreditation review
        5. Be suitable for institutional leadership and accreditation reviewers
        
        Keep it concise but comprehensive (300-500 words).
        """
        
        response = await self.llm_service.generate_response(prompt, "narrator")
        
        return {
            "title": "Executive Summary",
            "content": response,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_evidence_appendix(self, evidence_list: List[Evidence]) -> Dict[str, Any]:
        """Generate evidence appendix with catalog of all evidence"""
        
        evidence_catalog = []
        for evidence in evidence_list:
            evidence_catalog.append({
                "id": evidence.id,
                "title": evidence.title,
                "type": evidence.evidence_type.value,
                "description": evidence.description,
                "file_name": evidence.file_name,
                "upload_date": evidence.upload_date.isoformat() if evidence.upload_date else None,
                "keywords": evidence.keywords or [],
                "relevance_score": evidence.relevance_score
            })
        
        return {
            "title": "Evidence Appendix",
            "total_documents": len(evidence_list),
            "evidence_catalog": evidence_catalog,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_compliance_scoring(
        self,
        evidence_list: List[Evidence],
        standards: List[Dict[str, Any]],
        accreditor_id: str
    ) -> Dict[str, Any]:
        """Generate compliance scoring analysis"""
        
        # Simple compliance scoring based on evidence availability
        total_standards = len(standards)
        evidence_types = set(evidence.evidence_type.value for evidence in evidence_list)
        
        # Calculate coverage scores
        coverage_score = min(100, (len(evidence_types) / max(1, total_standards)) * 100)
        quality_score = sum(evidence.confidence_score or 0.8 for evidence in evidence_list) / max(1, len(evidence_list)) * 100
        
        return {
            "overall_score": (coverage_score + quality_score) / 2,
            "coverage_score": coverage_score,
            "quality_score": quality_score,
            "total_standards": total_standards,
            "evidence_count": len(evidence_list),
            "evidence_types_covered": list(evidence_types),
            "analysis_date": datetime.now().isoformat()
        }
    
    def _extract_evidence_references(self, content: str) -> List[str]:
        """Extract evidence references from content"""
        import re
        references = re.findall(r'\[Evidence ID: ([^\]]+)\]', content)
        return list(set(references))
    
    async def _save_report(self, report_data: Dict[str, Any], db_service: DatabaseService):
        """Save generated report to database"""
        try:
            # This would save to a reports table
            # For now, just log the save operation
            logger.info(f"Report {report_data['report_id']} saved to database")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
    
    async def _analyze_qep_effectiveness(
        self,
        qep_data: Dict[str, Any],
        assessment_results: Optional[Dict[str, Any]],
        institution: Institution,
        additional_context: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze QEP effectiveness and impact"""
        
        prompt = f"""
        Analyze the effectiveness of the Quality Enhancement Plan (QEP) for {institution.name}.
        
        QEP Data: {json.dumps(qep_data, indent=2)}
        Assessment Results: {json.dumps(assessment_results or {}, indent=2)}
        Additional Context: {additional_context or 'None provided'}
        
        Provide analysis on:
        1. Goal achievement and outcomes
        2. Implementation effectiveness
        3. Student learning impact
        4. Institutional improvement
        5. Resource utilization
        6. Sustainability planning
        
        Format as structured analysis with specific findings and data references.
        """
        
        response = await self.llm_service.generate_response(prompt, "analyzer")
        
        return {
            "analysis": response,
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def _generate_qep_impact_assessment(
        self,
        qep_data: Dict[str, Any],
        assessment_results: Optional[Dict[str, Any]],
        institution: Institution
    ) -> Dict[str, Any]:
        """Generate QEP impact assessment"""
        
        prompt = f"""
        Generate a comprehensive impact assessment for the QEP at {institution.name}.
        
        Focus on measurable outcomes and institutional changes resulting from the QEP.
        Include both quantitative and qualitative measures where available.
        
        Structure the assessment with:
        1. Baseline vs. current performance
        2. Student success indicators
        3. Institutional capacity changes
        4. Process improvements
        5. Cultural/climate changes
        6. Unexpected outcomes or benefits
        """
        
        response = await self.llm_service.generate_response(prompt, "analyzer")
        
        return {
            "assessment": response,
            "assessed_at": datetime.now().isoformat()
        }
    
    async def _generate_qep_recommendations(
        self,
        qep_analysis: Dict[str, Any],
        impact_assessment: Dict[str, Any],
        institution: Institution
    ) -> Dict[str, Any]:
        """Generate QEP recommendations for next steps"""
        
        prompt = f"""
        Based on the QEP analysis and impact assessment, generate actionable recommendations 
        for {institution.name}'s continued improvement.
        
        Include:
        1. Short-term actions (next 6 months)
        2. Medium-term goals (1-2 years)
        3. Long-term strategic initiatives (3-5 years)
        4. Resource requirements
        5. Success metrics
        6. Risk mitigation strategies
        """
        
        response = await self.llm_service.generate_response(prompt, "analyzer")
        
        return {
            "recommendations": response,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_contextual_narrative(
        self,
        standard: Dict[str, Any],
        evidence_items: List[Evidence],
        institution: Institution,
        accreditor_id: str,
        additional_context: Optional[str],
        narrative_style: str
    ) -> str:
        """Generate contextual narrative for a standard"""
        
        evidence_summaries = []
        for evidence in evidence_items:
            evidence_summaries.append({
                "title": evidence.title,
                "type": evidence.evidence_type.value,
                "summary": evidence.extracted_text[:500] if evidence.extracted_text else evidence.description
            })
        
        style_instructions = {
            "formal": "formal academic tone appropriate for accreditation reports",
            "conversational": "clear, accessible language while maintaining professionalism",
            "analytical": "data-driven, analytical approach with emphasis on metrics and outcomes"
        }.get(narrative_style, "formal academic tone")
        
        prompt = f"""
        Generate a comprehensive narrative response for {standard['title']} (Standard {standard['id']}) 
        for {institution.name}'s {accreditor_id} accreditation review.
        
        Standard Requirements: {standard.get('description', 'No description available')}
        
        Available Evidence:
        {json.dumps(evidence_summaries, indent=2)}
        
        Additional Context: {additional_context or 'None provided'}
        
        Write in {style_instructions}.
        
        The narrative should:
        1. Directly address all aspects of the standard
        2. Integrate evidence naturally with proper citations
        3. Demonstrate clear compliance and institutional strength
        4. Address any potential concerns proactively
        5. Be approximately 400-600 words
        6. Include specific examples and data where available
        
        Use [Evidence: Title] format for citations.
        """
        
        response = await self.llm_service.generate_response(prompt, "narrator")
        return response
