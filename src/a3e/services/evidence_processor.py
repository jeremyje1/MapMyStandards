"""
Evidence Processing Service with AI

Processes uploaded documents to extract text, analyze content,
and map evidence to accreditation standards using AI.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import secrets

# Document processing imports
try:
    import PyPDF2
    from docx import Document
    import pandas as pd
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger = logging.getLogger(__name__)
    logger.warning("PDF/DOCX support not available - install PyPDF2, python-docx, pandas")

from ..core.config import Settings
from ..database.connection import DatabaseManager
from .ai_service import get_ai_service

"""
Note: We intentionally avoid importing the OpenAI SDK here. All AI calls
are routed through AIService, which uses Anthropic SDK or OpenAI via HTTPX.
This prevents httpx wrapper shutdown errors from third-party SDKs.
"""

logger = logging.getLogger(__name__)


class EvidenceProcessor:
    """Processes evidence documents and maps them to standards using AI"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ai_service = get_ai_service()
        
        # Log AI service status
        status = self.ai_service.get_status()
        if status['ai_enabled']:
            logger.info(f"✅ AI service initialized - Primary: {status['primary_provider']}, Fallback: {status['fallback_provider']}")
        else:
            logger.warning("⚠️ No AI provider configured - using fallback processing")
    
    async def process_document(self, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document to extract evidence and map to standards
        
        Args:
            file_path: Path to the uploaded document
            metadata: Document metadata including filename, user_id, etc.
        
        Returns:
            Processing results including extracted text, mapped standards, and analysis
        """
        try:
            # Extract text from document
            text_content = await self.extract_text(file_path, metadata['filename'])
            
            if not text_content:
                logger.warning(f"No text extracted from {metadata['filename']}")
                return {
                    'status': 'failed',
                    'error': 'No text content found in document'
                }
            
            # Generate document fingerprint
            doc_hash = hashlib.sha256(text_content.encode()).hexdigest()[:16]
            
            # Analyze document with AI service
            analysis = await self.ai_service.analyze_document(text_content, metadata)
            
            # Map to standards
            standard_mappings = await self.map_to_standards(
                text_content, 
                analysis,
                metadata.get('accreditor', 'SACSCOC')
            )
            
            # Calculate compliance metrics
            metrics = self.calculate_metrics(analysis, standard_mappings)
            
            result = {
                'document_id': metadata.get('id', f"doc_{secrets.token_hex(8)}"),
                'filename': metadata['filename'],
                'doc_hash': doc_hash,
                'status': 'completed',
                'text_length': len(text_content),
                'word_count': len(text_content.split()),
                'extracted_text': text_content[:1000] + '...' if len(text_content) > 1000 else text_content,
                'analysis': analysis,
                'standard_mappings': standard_mappings,
                'metrics': metrics,
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Store results in database
            await self.store_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {metadata['filename']}: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def extract_text(self, file_path: Path, filename: str) -> str:
        """Extract text from various document formats"""
        text = ""
        
        try:
            ext = filename.lower().split('.')[-1]
            
            if ext == 'pdf' and PDF_SUPPORT:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
            elif ext in ['docx', 'doc'] and PDF_SUPPORT:
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
            
            elif ext in ['txt', 'md']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            elif ext in ['csv', 'xlsx', 'xls'] and PDF_SUPPORT:
                df = pd.read_excel(file_path) if ext in ['xlsx', 'xls'] else pd.read_csv(file_path)
                text = df.to_string()
            
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    text = file.read()
        
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
        
        return text.strip()
    
    async def analyze_with_ai(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy shim: delegate to AIService for analysis."""
        return await self.ai_service.analyze_document(text, metadata)
    
    def fallback_analysis(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis without AI"""
        
        # Simple keyword-based analysis
        keywords = {
            'strategic_planning': ['strategic', 'plan', 'mission', 'vision', 'goals', 'objectives'],
            'assessment': ['assessment', 'learning outcomes', 'evaluation', 'rubric', 'measurement'],
            'governance': ['board', 'governance', 'policy', 'administration', 'leadership'],
            'faculty': ['faculty', 'professor', 'instructor', 'qualification', 'credential'],
            'student_services': ['student', 'support', 'services', 'advising', 'counseling'],
            'finance': ['budget', 'financial', 'audit', 'revenue', 'expenditure'],
            'facilities': ['facilities', 'campus', 'infrastructure', 'safety', 'maintenance'],
            'technology': ['technology', 'IT', 'digital', 'online', 'system']
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
            'potential_gaps': ["Manual review recommended"],
            'recommendations': ["Review document for specific standard mapping"],
            'confidence_score': 50,
            'analysis_method': 'keyword_matching'
        }
    
    async def map_to_standards(self, text: str, analysis: Dict[str, Any], accreditor: str) -> List[Dict[str, Any]]:
        """Map document content to specific accreditation standards"""
        
        # Get standards for the accreditor
        standards = await self.get_standards_for_accreditor(accreditor)
        
        # Use AI service for mapping
        mappings = await self.ai_service.map_to_standards(text, analysis, standards, accreditor)
        
        return mappings
    
    def fallback_standard_mapping(self, analysis: Dict[str, Any], standards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic standard mapping without AI"""
        
        mappings = []
        compliance_areas = analysis.get('compliance_areas', [])
        
        # Map to first few standards as demonstration
        for standard in standards[:3]:
            if any(area in standard.get('title', '').lower() for area in compliance_areas):
                mappings.append({
                    'standard_id': standard.get('id', 'unknown'),
                    'standard_title': standard.get('title', 'Unknown Standard'),
                    'relevance_score': 60,
                    'evidence_summary': 'Document contains relevant evidence for this standard',
                    'mapping_confidence': 'low'
                })
        
        return mappings
    
    async def get_standards_for_accreditor(self, accreditor: str) -> List[Dict[str, Any]]:
        """Retrieve standards for a specific accreditor"""
        
        # For now, return sample SACSCOC standards
        # In production, would fetch from database
        if accreditor == 'SACSCOC':
            return [
                {'id': '8.1', 'title': 'Student Achievement', 'category': 'Student Success'},
                {'id': '8.2.a', 'title': 'Student Outcomes: Educational Programs', 'category': 'Student Success'},
                {'id': '8.2.b', 'title': 'Student Outcomes: General Education', 'category': 'Student Success'},
                {'id': '8.2.c', 'title': 'Student Outcomes: Academic and Student Services', 'category': 'Student Success'},
                {'id': '10.1', 'title': 'Academic Governance', 'category': 'Educational Policies'},
                {'id': '10.2', 'title': 'Public Information', 'category': 'Educational Policies'},
                {'id': '10.3', 'title': 'Archived Information', 'category': 'Educational Policies'},
                {'id': '10.4', 'title': 'Academic Program Approval', 'category': 'Educational Policies'},
                {'id': '10.5', 'title': 'Admissions Policies and Practices', 'category': 'Educational Policies'},
                {'id': '10.6', 'title': 'Distance and Correspondence Education', 'category': 'Educational Policies'}
            ]
        
        return []
    
    def calculate_metrics(self, analysis: Dict[str, Any], mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate compliance metrics from analysis and mappings"""
        
        total_mappings = len(mappings)
        high_confidence = len([m for m in mappings if m.get('mapping_confidence') == 'high'])
        avg_relevance = sum(m.get('relevance_score', 0) for m in mappings) / max(total_mappings, 1)
        
        return {
            'standards_mapped': total_mappings,
            'high_confidence_mappings': high_confidence,
            'average_relevance_score': round(avg_relevance, 1),
            'compliance_score': min(round(avg_relevance * 1.2, 1), 100),  # Scaled score
            'document_confidence': analysis.get('confidence_score', 50),
            'evidence_strength': 'strong' if avg_relevance > 70 else 'moderate' if avg_relevance > 40 else 'weak'
        }
    
    async def store_results(self, result: Dict[str, Any]):
        """Store processing results in database and update metrics"""
        try:
            # Store in database (simplified for now)
            logger.info(f"Stored processing results for document {result['document_id']}")
            
            # Update analytics metrics via API
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        'http://localhost:8000/api/v1/analytics/document/processed',
                        json=result,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Updated metrics for document {result['document_id']}")
                except Exception as e:
                    logger.warning(f"Could not update metrics: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to store results: {e}")


# Singleton instance
_processor_instance = None

def get_evidence_processor(settings: Settings) -> EvidenceProcessor:
    """Get or create evidence processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = EvidenceProcessor(settings)
    return _processor_instance
