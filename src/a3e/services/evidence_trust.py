"""
EvidenceTrust Score™ - Multi-factor evidence quality and trust scoring
Evaluates provenance, freshness, completeness, relevance, and alignment
"""

import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SourceSystem(Enum):
    """Evidence source system types"""
    MANUAL = "manual"
    LMS = "lms"  # Learning Management System
    ERP = "erp"  # Enterprise Resource Planning
    SIS = "sis"  # Student Information System
    SURVEY = "survey"
    EXTERNAL_AUDIT = "external_audit"
    INTERNAL_SYSTEM = "internal_system"


class EvidenceType(Enum):
    """Types of evidence documents"""
    POLICY = "policy"
    PROCEDURE = "procedure"
    SYLLABUS = "syllabus"
    ASSESSMENT = "assessment"
    REPORT = "report"
    MEETING_MINUTES = "meeting_minutes"
    SURVEY_RESULTS = "survey_results"
    FINANCIAL_STATEMENT = "financial_statement"
    CURRICULUM = "curriculum"
    FACULTY_CREDENTIAL = "faculty_credential"


@dataclass
class TrustSignal:
    """Individual trust signal for evidence"""
    signal_type: str
    value: float  # 0-1 normalized value
    weight: float  # Importance weight
    explanation: str
    
    def weighted_value(self) -> float:
        return self.value * self.weight


@dataclass
class EvidenceTrustScore:
    """Complete trust score for a piece of evidence"""
    evidence_id: str
    overall_score: float  # 0-1 overall trust score
    signals: List[TrustSignal]
    trust_level: str  # 'high', 'medium', 'low', 'critical'
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'overall_score': round(self.overall_score, 3),
            'trust_level': self.trust_level,
            'signals': [
                {
                    'type': s.signal_type,
                    'value': round(s.value, 3),
                    'weight': s.weight,
                    'explanation': s.explanation
                }
                for s in self.signals
            ],
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


class EvidenceTrustScorer:
    """Calculates multi-factor trust scores for evidence"""
    
    def __init__(self):
        self.weights = {
            'provenance': 0.20,
            'freshness': 0.25,
            'completeness': 0.15,
            'relevance': 0.20,
            'alignment': 0.10,
            'reviewer_verification': 0.10
        }
        
        self.freshness_thresholds = {
            EvidenceType.POLICY: 365 * 2,  # 2 years
            EvidenceType.SYLLABUS: 180,  # 6 months
            EvidenceType.ASSESSMENT: 365,  # 1 year
            EvidenceType.FINANCIAL_STATEMENT: 365,  # 1 year
            EvidenceType.SURVEY_RESULTS: 365 * 2,  # 2 years
            EvidenceType.MEETING_MINUTES: 30,  # 1 month
            EvidenceType.REPORT: 365,  # 1 year
            EvidenceType.CURRICULUM: 365 * 3,  # 3 years
            EvidenceType.FACULTY_CREDENTIAL: 365 * 5,  # 5 years
            EvidenceType.PROCEDURE: 365 * 2  # 2 years
        }
    
    def calculate_trust_score(
        self,
        evidence_id: str,
        evidence_type: EvidenceType,
        source_system: SourceSystem,
        upload_date: datetime,
        last_modified: datetime,
        content_length: int,
        metadata: Dict[str, Any],
        mapping_confidence: Optional[float] = None,
        reviewer_approved: bool = False,
        citations_count: int = 0,
        conflicts_detected: int = 0
    ) -> EvidenceTrustScore:
        """Calculate comprehensive trust score for evidence"""
        
        signals = []
        
        # 1. Provenance Score
        provenance_signal = self._calculate_provenance_score(
            source_system, metadata
        )
        signals.append(provenance_signal)
        
        # 2. Freshness Score
        freshness_signal = self._calculate_freshness_score(
            evidence_type, last_modified
        )
        signals.append(freshness_signal)
        
        # 3. Completeness Score
        completeness_signal = self._calculate_completeness_score(
            content_length, evidence_type, metadata
        )
        signals.append(completeness_signal)
        
        # 4. Relevance Score
        relevance_signal = self._calculate_relevance_score(
            mapping_confidence, citations_count
        )
        signals.append(relevance_signal)
        
        # 5. Alignment Score
        alignment_signal = self._calculate_alignment_score(
            conflicts_detected, metadata
        )
        signals.append(alignment_signal)
        
        # 6. Reviewer Verification Score
        verification_signal = self._calculate_verification_score(
            reviewer_approved, metadata
        )
        signals.append(verification_signal)
        
        # Calculate overall score
        overall_score = sum(s.weighted_value() for s in signals) / sum(s.weight for s in signals)
        
        # Determine trust level
        trust_level = self._determine_trust_level(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(signals, evidence_type)
        
        return EvidenceTrustScore(
            evidence_id=evidence_id,
            overall_score=overall_score,
            signals=signals,
            trust_level=trust_level,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )
    
    def _calculate_provenance_score(
        self,
        source_system: SourceSystem,
        metadata: Dict[str, Any]
    ) -> TrustSignal:
        """Calculate provenance trust score"""
        
        # Base scores by source system
        system_scores = {
            SourceSystem.EXTERNAL_AUDIT: 1.0,
            SourceSystem.ERP: 0.9,
            SourceSystem.LMS: 0.85,
            SourceSystem.SIS: 0.85,
            SourceSystem.INTERNAL_SYSTEM: 0.7,
            SourceSystem.SURVEY: 0.6,
            SourceSystem.MANUAL: 0.5
        }
        
        base_score = system_scores.get(source_system, 0.5)
        
        # Adjust for additional metadata
        if metadata.get('digital_signature'):
            base_score = min(1.0, base_score + 0.1)
        
        if metadata.get('audit_trail'):
            base_score = min(1.0, base_score + 0.05)
        
        explanation = f"Source: {source_system.value} system"
        if source_system == SourceSystem.EXTERNAL_AUDIT:
            explanation += " (highest trust - external verification)"
        elif source_system == SourceSystem.MANUAL:
            explanation += " (requires additional verification)"
        
        return TrustSignal(
            signal_type='provenance',
            value=base_score,
            weight=self.weights['provenance'],
            explanation=explanation
        )
    
    def _calculate_freshness_score(
        self,
        evidence_type: EvidenceType,
        last_modified: datetime
    ) -> TrustSignal:
        """Calculate freshness trust score based on document age"""
        
        age_days = (datetime.utcnow() - last_modified).days
        threshold_days = self.freshness_thresholds.get(evidence_type, 365)
        
        # Exponential decay function
        if age_days <= threshold_days / 4:
            score = 1.0  # Very fresh
        elif age_days <= threshold_days / 2:
            score = 0.9  # Fresh
        elif age_days <= threshold_days:
            score = 0.7  # Acceptable
        elif age_days <= threshold_days * 1.5:
            score = 0.5  # Getting stale
        elif age_days <= threshold_days * 2:
            score = 0.3  # Stale
        else:
            score = 0.1  # Very stale
        
        explanation = f"Document age: {age_days} days"
        if score >= 0.9:
            explanation += " (very current)"
        elif score >= 0.7:
            explanation += " (acceptably current)"
        elif score >= 0.5:
            explanation += " (needs update soon)"
        else:
            explanation += " (requires immediate update)"
        
        return TrustSignal(
            signal_type='freshness',
            value=score,
            weight=self.weights['freshness'],
            explanation=explanation
        )
    
    def _calculate_completeness_score(
        self,
        content_length: int,
        evidence_type: EvidenceType,
        metadata: Dict[str, Any]
    ) -> TrustSignal:
        """Calculate completeness score based on content analysis"""
        
        # Minimum expected lengths by type
        min_lengths = {
            EvidenceType.POLICY: 1000,
            EvidenceType.SYLLABUS: 2000,
            EvidenceType.ASSESSMENT: 500,
            EvidenceType.REPORT: 3000,
            EvidenceType.MEETING_MINUTES: 500,
            EvidenceType.FINANCIAL_STATEMENT: 1000
        }
        
        min_expected = min_lengths.get(evidence_type, 1000)
        
        # Base score from content length
        if content_length >= min_expected * 2:
            base_score = 1.0
        elif content_length >= min_expected:
            base_score = 0.8
        elif content_length >= min_expected * 0.5:
            base_score = 0.5
        else:
            base_score = 0.3
        
        # Adjust for metadata completeness
        required_fields = metadata.get('required_fields', [])
        provided_fields = metadata.get('provided_fields', [])
        
        if required_fields:
            field_completeness = len(provided_fields) / len(required_fields)
            base_score = (base_score + field_completeness) / 2
        
        explanation = f"Content length: {content_length} characters"
        if base_score >= 0.8:
            explanation += " (comprehensive)"
        elif base_score >= 0.5:
            explanation += " (adequate)"
        else:
            explanation += " (may be incomplete)"
        
        return TrustSignal(
            signal_type='completeness',
            value=base_score,
            weight=self.weights['completeness'],
            explanation=explanation
        )
    
    def _calculate_relevance_score(
        self,
        mapping_confidence: Optional[float],
        citations_count: int
    ) -> TrustSignal:
        """Calculate relevance score based on mapping and citations"""
        
        if mapping_confidence is not None:
            base_score = mapping_confidence
        else:
            base_score = 0.5  # Neutral if no mapping available
        
        # Boost for citations
        if citations_count > 10:
            base_score = min(1.0, base_score + 0.2)
        elif citations_count > 5:
            base_score = min(1.0, base_score + 0.1)
        elif citations_count > 0:
            base_score = min(1.0, base_score + 0.05)
        
        explanation = f"Mapping confidence: {mapping_confidence:.1%}" if mapping_confidence else "No mapping available"
        if citations_count > 0:
            explanation += f", cited {citations_count} times"
        
        return TrustSignal(
            signal_type='relevance',
            value=base_score,
            weight=self.weights['relevance'],
            explanation=explanation
        )
    
    def _calculate_alignment_score(
        self,
        conflicts_detected: int,
        metadata: Dict[str, Any]
    ) -> TrustSignal:
        """Calculate alignment score based on conflicts and consistency"""
        
        # Start with perfect alignment
        score = 1.0
        
        # Deduct for conflicts
        if conflicts_detected > 0:
            score -= min(0.5, conflicts_detected * 0.1)
        
        # Check for duplication
        if metadata.get('is_duplicate'):
            score -= 0.2
        
        # Check for superseded versions
        if metadata.get('is_superseded'):
            score -= 0.3
        
        score = max(0, score)
        
        explanation = "No conflicts detected" if conflicts_detected == 0 else f"{conflicts_detected} conflicts found"
        if metadata.get('is_duplicate'):
            explanation += " (duplicate content)"
        if metadata.get('is_superseded'):
            explanation += " (superseded version)"
        
        return TrustSignal(
            signal_type='alignment',
            value=score,
            weight=self.weights['alignment'],
            explanation=explanation
        )
    
    def _calculate_verification_score(
        self,
        reviewer_approved: bool,
        metadata: Dict[str, Any]
    ) -> TrustSignal:
        """Calculate verification score based on review status"""
        
        if reviewer_approved:
            score = 1.0
            explanation = "Reviewer approved"
        else:
            score = 0.3
            explanation = "Pending review"
        
        # Additional verification signals
        if metadata.get('multi_reviewer_approved'):
            score = 1.0
            explanation = "Multiple reviewers approved"
        elif metadata.get('auto_verified'):
            score = 0.7
            explanation = "Auto-verified by system"
        
        return TrustSignal(
            signal_type='reviewer_verification',
            value=score,
            weight=self.weights['reviewer_verification'],
            explanation=explanation
        )
    
    def _determine_trust_level(self, overall_score: float) -> str:
        """Determine categorical trust level from score"""
        if overall_score >= 0.8:
            return 'high'
        elif overall_score >= 0.6:
            return 'medium'
        elif overall_score >= 0.4:
            return 'low'
        else:
            return 'critical'
    
    def _generate_recommendations(
        self,
        signals: List[TrustSignal],
        evidence_type: EvidenceType
    ) -> List[str]:
        """Generate actionable recommendations based on trust signals"""
        
        recommendations = []
        
        for signal in signals:
            if signal.signal_type == 'freshness' and signal.value < 0.5:
                recommendations.append(f"Update this {evidence_type.value} - it's {int((1-signal.value)*100)}% stale")
            
            elif signal.signal_type == 'completeness' and signal.value < 0.6:
                recommendations.append("Add missing content or required fields")
            
            elif signal.signal_type == 'reviewer_verification' and signal.value < 0.5:
                recommendations.append("Submit for reviewer approval")
            
            elif signal.signal_type == 'provenance' and signal.value < 0.6:
                recommendations.append("Consider sourcing from authoritative system")
            
            elif signal.signal_type == 'alignment' and signal.value < 0.7:
                recommendations.append("Resolve conflicts or duplications")
        
        if not recommendations and overall_score < 0.7:
            recommendations.append("Consider replacing with higher-quality evidence")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def batch_score_evidence(
        self,
        evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, EvidenceTrustScore]:
        """Batch process multiple evidence items"""
        scores = {}
        
        for evidence in evidence_list:
            score = self.calculate_trust_score(
                evidence_id=evidence['id'],
                evidence_type=EvidenceType(evidence['type']),
                source_system=SourceSystem(evidence['source']),
                upload_date=evidence['upload_date'],
                last_modified=evidence['last_modified'],
                content_length=evidence.get('content_length', 0),
                metadata=evidence.get('metadata', {}),
                mapping_confidence=evidence.get('mapping_confidence'),
                reviewer_approved=evidence.get('reviewer_approved', False),
                citations_count=evidence.get('citations_count', 0),
                conflicts_detected=evidence.get('conflicts_detected', 0)
            )
            scores[evidence['id']] = score
        
        return scores
    
    def get_trust_statistics(self, scores: Dict[str, EvidenceTrustScore]) -> Dict[str, Any]:
        """Generate statistics for a set of trust scores"""
        if not scores:
            return {'total': 0}
        
        all_scores = [s.overall_score for s in scores.values()]
        
        stats = {
            'total': len(scores),
            'average_trust': np.mean(all_scores),
            'median_trust': np.median(all_scores),
            'by_level': {
                'high': sum(1 for s in scores.values() if s.trust_level == 'high'),
                'medium': sum(1 for s in scores.values() if s.trust_level == 'medium'),
                'low': sum(1 for s in scores.values() if s.trust_level == 'low'),
                'critical': sum(1 for s in scores.values() if s.trust_level == 'critical')
            },
            'needs_review': sum(1 for s in scores.values() if s.overall_score < 0.6),
            'needs_update': sum(
                1 for s in scores.values()
                if any(sig.signal_type == 'freshness' and sig.value < 0.5 for sig in s.signals)
            )
        }
        
        return stats


# Global instance
evidence_trust_scorer = EvidenceTrustScorer()