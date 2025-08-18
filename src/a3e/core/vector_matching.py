"""
Proprietary Vector-Weighted Standards Matching Algorithm for A³E
Advanced semantic similarity and standards alignment engine
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import uuid

# Optional scientific computing imports
try:
    import numpy as np
    from scipy.spatial.distance import cosine
    from sklearn.metrics.pairwise import cosine_similarity
    SCIENTIFIC_FEATURES_AVAILABLE = True
except ImportError:
    SCIENTIFIC_FEATURES_AVAILABLE = False
    # Mock implementations for basic functionality
    class MockNdarray:
        def __init__(self, data):
            self.data = data
    
    class np:
        ndarray = MockNdarray  # For type hints
        
        @staticmethod
        def array(data):
            return MockNdarray(data)
        
        @staticmethod
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))
    
    def cosine_similarity(a, b):
        return [[1.0]]  # Simple fallback
    
    def cosine(a, b):
        return 0.0  # Simple fallback

from .accreditation_ontology import AccreditationOntology, AccreditationDomain, EvidenceType, StandardComplexity

logger = logging.getLogger(__name__)

class MatchingStrategy(Enum):
    """Matching strategies for different use cases."""
    EXACT_SEMANTIC = "exact_semantic"           # High precision, semantic similarity
    INFERENTIAL = "inferential"                 # Medium precision, requires inference
    CROSS_DOMAIN = "cross_domain"              # Low precision, cross-domain synthesis
    EMERGENT_PATTERN = "emergent_pattern"      # Complex pattern recognition

@dataclass
class MatchingWeight:
    """Configurable weights for different matching factors."""
    semantic_similarity: float = 0.35
    ontology_hierarchy: float = 0.25
    domain_relevance: float = 0.20
    evidence_alignment: float = 0.15
    temporal_relevance: float = 0.05
    
    def normalize(self) -> 'MatchingWeight':
        """Normalize weights to sum to 1.0."""
        total = (self.semantic_similarity + self.ontology_hierarchy + 
                self.domain_relevance + self.evidence_alignment + self.temporal_relevance)
        
        return MatchingWeight(
            semantic_similarity=self.semantic_similarity / total,
            ontology_hierarchy=self.ontology_hierarchy / total,
            domain_relevance=self.domain_relevance / total,
            evidence_alignment=self.evidence_alignment / total,
            temporal_relevance=self.temporal_relevance / total
        )

@dataclass
class StandardMatch:
    """Represents a match between evidence and a standard."""
    standard_id: str
    evidence_id: str
    confidence_score: float
    match_type: MatchingStrategy
    complexity_level: StandardComplexity
    
    # Detailed scoring breakdown
    semantic_score: float
    hierarchy_score: float
    domain_score: float
    evidence_score: float
    temporal_score: float
    
    # Supporting information
    matched_concepts: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    
    # Audit trail
    match_timestamp: datetime = field(default_factory=datetime.utcnow)
    match_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Quality indicators
    reliability_score: float = 0.0
    verification_status: str = "pending"

@dataclass 
class EvidenceDocument:
    """Represents a piece of evidence with embeddings and metadata."""
    id: str
    content: str
    title: str
    evidence_type: EvidenceType
    
    # Embeddings
    content_embedding: np.ndarray
    title_embedding: np.ndarray
    
    # Metadata
    source_system: str
    collection_date: datetime
    domain_tags: List[AccreditationDomain] = field(default_factory=list)
    quality_score: float = 0.0
    
    # Ontology mappings
    mapped_concepts: List[str] = field(default_factory=list)
    inferred_concepts: List[str] = field(default_factory=list)

class VectorWeightedMatcher:
    """Proprietary vector-weighted standards matching algorithm."""
    
    def __init__(self, ontology: AccreditationOntology):
        self.ontology = ontology
        self.default_weights = MatchingWeight().normalize()
        self.match_cache: Dict[str, List[StandardMatch]] = {}
        
        # Algorithm parameters
        self.min_confidence_threshold = 0.7
        self.semantic_similarity_threshold = 0.75
        self.hierarchy_boost_factor = 0.1
        self.domain_penalty_factor = 0.2
        
    def match_evidence_to_standards(self, 
                                   evidence: EvidenceDocument,
                                   standards: List[str],
                                   strategy: MatchingStrategy = MatchingStrategy.EXACT_SEMANTIC,
                                   custom_weights: Optional[MatchingWeight] = None) -> List[StandardMatch]:
        """
        Match evidence to standards using proprietary vector-weighted algorithm.
        
        Args:
            evidence: The evidence document to match
            standards: List of standard IDs to match against
            strategy: Matching strategy to use
            custom_weights: Custom weights for matching factors
            
        Returns:
            List of StandardMatch objects sorted by confidence
        """
        
        weights = custom_weights.normalize() if custom_weights else self.default_weights
        
        # Generate cache key
        cache_key = f"{evidence.id}_{hash(tuple(standards))}_{strategy.value}"
        if cache_key in self.match_cache:
            return self.match_cache[cache_key]
        
        matches = []
        
        for standard_id in standards:
            if standard_id not in self.ontology.nodes:
                continue
                
            match = self._compute_standard_match(evidence, standard_id, strategy, weights)
            if match and match.confidence_score >= self.min_confidence_threshold:
                matches.append(match)
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Cache results
        self.match_cache[cache_key] = matches
        
        return matches
    
    def _compute_standard_match(self, 
                               evidence: EvidenceDocument,
                               standard_id: str,
                               strategy: MatchingStrategy,
                               weights: MatchingWeight) -> Optional[StandardMatch]:
        """Compute match between evidence and a single standard."""
        
        standard_node = self.ontology.nodes[standard_id]
        
        # 1. Semantic Similarity Score
        semantic_score = self._compute_semantic_similarity(evidence, standard_node)
        
        # 2. Ontology Hierarchy Score
        hierarchy_score = self._compute_hierarchy_score(evidence, standard_node)
        
        # 3. Domain Relevance Score
        domain_score = self._compute_domain_relevance(evidence, standard_node)
        
        # 4. Evidence Alignment Score
        evidence_score = self._compute_evidence_alignment(evidence, standard_node)
        
        # 5. Temporal Relevance Score
        temporal_score = self._compute_temporal_relevance(evidence, standard_node)
        
        # Strategy-specific adjustments
        semantic_score, hierarchy_score, domain_score, evidence_score, temporal_score = \
            self._apply_strategy_adjustments(
                strategy, semantic_score, hierarchy_score, domain_score, evidence_score, temporal_score
            )
        
        # Compute weighted final score
        confidence_score = (
            weights.semantic_similarity * semantic_score +
            weights.ontology_hierarchy * hierarchy_score +
            weights.domain_relevance * domain_score +
            weights.evidence_alignment * evidence_score +
            weights.temporal_relevance * temporal_score
        )
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(
            semantic_score, hierarchy_score, domain_score, evidence_score
        )
        
        # Compute reliability score
        reliability_score = self._compute_reliability_score(
            [semantic_score, hierarchy_score, domain_score, evidence_score, temporal_score]
        )
        
        # Find supporting concepts and gaps
        matched_concepts, evidence_gaps, supporting_evidence = self._analyze_match_details(
            evidence, standard_node, semantic_score
        )
        
        return StandardMatch(
            standard_id=standard_id,
            evidence_id=evidence.id,
            confidence_score=confidence_score,
            match_type=strategy,
            complexity_level=complexity_level,
            semantic_score=semantic_score,
            hierarchy_score=hierarchy_score,
            domain_score=domain_score,
            evidence_score=evidence_score,
            temporal_score=temporal_score,
            matched_concepts=matched_concepts,
            evidence_gaps=evidence_gaps,
            supporting_evidence=supporting_evidence,
            reliability_score=reliability_score
        )
    
    def _compute_semantic_similarity(self, evidence: EvidenceDocument, standard_node) -> float:
        """Compute semantic similarity using proprietary embeddings."""
        
        if standard_node.embedding_vector is None:
            return 0.0
        
        # Use content embedding for primary similarity
        content_sim = 1 - cosine(evidence.content_embedding, standard_node.embedding_vector)
        
        # Use title embedding for secondary similarity
        title_sim = 1 - cosine(evidence.title_embedding, standard_node.embedding_vector)
        
        # Weighted combination (content is more important)
        semantic_score = 0.8 * content_sim + 0.2 * title_sim
        
        # Apply domain-specific embedding weights
        domain_boost = self._get_domain_embedding_boost(evidence, standard_node)
        semantic_score = min(1.0, semantic_score * (1 + domain_boost))
        
        return max(0.0, semantic_score)
    
    def _compute_hierarchy_score(self, evidence: EvidenceDocument, standard_node) -> float:
        """Compute score based on ontology hierarchy relationships."""
        
        score = 0.0
        
        # Direct concept matches
        for concept_id in evidence.mapped_concepts:
            if concept_id == standard_node.id:
                score += 1.0
            elif concept_id in standard_node.children_ids:
                score += 0.8
            elif standard_node.id in self.ontology.get_concept_hierarchy(concept_id):
                score += 0.6
        
        # Inferred concept matches (lower weight)
        for concept_id in evidence.inferred_concepts:
            if concept_id == standard_node.id:
                score += 0.7
            elif concept_id in standard_node.children_ids:
                score += 0.5
        
        # Related concept matches
        related_concepts = [rel[0] for rel in self.ontology.find_related_concepts(standard_node.id)]
        for concept_id in evidence.mapped_concepts + evidence.inferred_concepts:
            if concept_id in related_concepts:
                score += 0.3
        
        # Normalize by potential maximum score
        max_possible = len(evidence.mapped_concepts) + len(evidence.inferred_concepts)
        if max_possible > 0:
            score = score / max_possible
        
        return min(1.0, score)
    
    def _compute_domain_relevance(self, evidence: EvidenceDocument, standard_node) -> float:
        """Compute relevance based on accreditation domains."""
        
        if not evidence.domain_tags:
            return 0.5  # Neutral score if no domain tags
        
        # Direct domain match
        if standard_node.domain in evidence.domain_tags:
            return 1.0
        
        # Cross-domain relevance matrix (simplified)
        domain_relevance_matrix = {
            AccreditationDomain.MISSION_GOVERNANCE: [
                AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS,
                AccreditationDomain.FINANCIAL_RESOURCES
            ],
            AccreditationDomain.ACADEMIC_PROGRAMS: [
                AccreditationDomain.STUDENT_SUCCESS,
                AccreditationDomain.FACULTY_RESOURCES,
                AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS
            ],
            AccreditationDomain.STUDENT_SUCCESS: [
                AccreditationDomain.ACADEMIC_PROGRAMS,
                AccreditationDomain.FACULTY_RESOURCES
            ],
            AccreditationDomain.FACULTY_RESOURCES: [
                AccreditationDomain.ACADEMIC_PROGRAMS,
                AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS
            ],
            AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS: [
                AccreditationDomain.MISSION_GOVERNANCE,
                AccreditationDomain.ACADEMIC_PROGRAMS,
                AccreditationDomain.FACULTY_RESOURCES
            ],
            AccreditationDomain.FINANCIAL_RESOURCES: [
                AccreditationDomain.MISSION_GOVERNANCE,
                AccreditationDomain.INFRASTRUCTURE
            ],
            AccreditationDomain.INFRASTRUCTURE: [
                AccreditationDomain.FINANCIAL_RESOURCES,
                AccreditationDomain.COMPLIANCE_ETHICS
            ],
            AccreditationDomain.COMPLIANCE_ETHICS: [
                AccreditationDomain.INFRASTRUCTURE,
                AccreditationDomain.MISSION_GOVERNANCE
            ]
        }
        
        # Check for related domain matches
        related_domains = domain_relevance_matrix.get(standard_node.domain, [])
        for domain in evidence.domain_tags:
            if domain in related_domains:
                return 0.7
        
        return 0.2  # Low relevance for unrelated domains
    
    def _compute_evidence_alignment(self, evidence: EvidenceDocument, standard_node) -> float:
        """Compute alignment between evidence type and required evidence types."""
        
        if not standard_node.required_evidence_types:
            return 0.5  # Neutral if no specific requirements
        
        # Direct evidence type match
        if evidence.evidence_type in standard_node.required_evidence_types:
            return min(1.0, evidence.quality_score + 0.2)  # Boost for quality
        
        # Evidence type compatibility matrix
        evidence_compatibility = {
            EvidenceType.POLICY_DOCUMENT: [
                EvidenceType.GOVERNANCE_RECORD,
                EvidenceType.COMPLIANCE_ETHICS
            ],
            EvidenceType.ASSESSMENT_DATA: [
                EvidenceType.LEARNING_OUTCOME,
                EvidenceType.STUDENT_RECORD
            ],
            EvidenceType.CURRICULUM_ARTIFACT: [
                EvidenceType.LEARNING_OUTCOME,
                EvidenceType.ASSESSMENT_DATA
            ],
            EvidenceType.FACULTY_CREDENTIAL: [
                EvidenceType.EXTERNAL_VALIDATION
            ]
        }
        
        # Check compatible evidence types
        compatible_types = evidence_compatibility.get(evidence.evidence_type, [])
        for req_type in standard_node.required_evidence_types:
            if req_type in compatible_types:
                return 0.7
        
        return 0.3  # Low alignment for incompatible evidence types
    
    def _compute_temporal_relevance(self, evidence: EvidenceDocument, standard_node) -> float:
        """Compute temporal relevance based on assessment frequency and evidence age."""
        
        # Evidence age in days
        evidence_age = (datetime.utcnow() - evidence.collection_date).days
        
        # Default temporal relevance based on evidence age
        if evidence_age <= 30:
            base_score = 1.0
        elif evidence_age <= 90:
            base_score = 0.9
        elif evidence_age <= 365:
            base_score = 0.7
        elif evidence_age <= 1095:  # 3 years
            base_score = 0.5
        else:
            base_score = 0.2
        
        # Adjust based on assessment frequency
        if standard_node.assessment_frequency:
            if "annual" in standard_node.assessment_frequency.lower():
                if evidence_age > 365:
                    base_score *= 0.5
            elif "triennial" in standard_node.assessment_frequency.lower():
                if evidence_age > 1095:
                    base_score *= 0.3
        
        return base_score
    
    def _apply_strategy_adjustments(self, strategy: MatchingStrategy, 
                                   semantic: float, hierarchy: float, domain: float,
                                   evidence: float, temporal: float) -> Tuple[float, float, float, float, float]:
        """Apply strategy-specific score adjustments."""
        
        if strategy == MatchingStrategy.EXACT_SEMANTIC:
            # Boost semantic similarity, penalize low hierarchy scores
            semantic *= 1.2
            if hierarchy < 0.5:
                hierarchy *= 0.7
                
        elif strategy == MatchingStrategy.INFERENTIAL:
            # Boost hierarchy and domain scores
            hierarchy *= 1.1
            domain *= 1.1
            semantic *= 0.9
            
        elif strategy == MatchingStrategy.CROSS_DOMAIN:
            # Reduce domain penalty, boost evidence alignment
            domain = max(domain, 0.5)
            evidence *= 1.2
            
        elif strategy == MatchingStrategy.EMERGENT_PATTERN:
            # Balance all factors, boost complexity handling
            semantic *= 0.95
            hierarchy *= 1.05
            domain *= 1.05
            evidence *= 1.05
        
        # Ensure scores stay in [0, 1] range
        return (min(1.0, max(0.0, score)) for score in [semantic, hierarchy, domain, evidence, temporal])
    
    def _determine_complexity_level(self, semantic: float, hierarchy: float, 
                                   domain: float, evidence: float) -> StandardComplexity:
        """Determine the complexity level of the match."""
        
        # High scores across the board = DIRECT
        if all(score >= 0.8 for score in [semantic, hierarchy, domain, evidence]):
            return StandardComplexity.DIRECT
        
        # Good semantic and hierarchy but poor domain/evidence = INFERENTIAL
        if semantic >= 0.7 and hierarchy >= 0.7 and (domain < 0.6 or evidence < 0.6):
            return StandardComplexity.INFERENTIAL
        
        # Cross-domain synthesis required
        if domain < 0.5 and semantic >= 0.6:
            return StandardComplexity.SYNTHETIC
        
        # Complex pattern recognition needed
        return StandardComplexity.EMERGENT
    
    def _compute_reliability_score(self, scores: List[float]) -> float:
        """Compute reliability score based on score consistency."""
        
        if not scores:
            return 0.0
        
        # Measure consistency using standard deviation
        mean_score = np.mean(scores)
        std_dev = np.std(scores)
        
        # Lower standard deviation = higher reliability
        consistency_score = 1.0 - min(1.0, std_dev / mean_score if mean_score > 0 else 1.0)
        
        # Boost reliability for high overall scores
        if mean_score >= 0.8:
            consistency_score *= 1.1
        
        return min(1.0, consistency_score)
    
    def _analyze_match_details(self, evidence: EvidenceDocument, standard_node, semantic_score: float) -> Tuple[List[str], List[str], List[str]]:
        """Analyze detailed match information for audit trails."""
        
        matched_concepts = []
        evidence_gaps = []
        supporting_evidence = []
        
        # Find matched concepts
        for concept_id in evidence.mapped_concepts:
            if (concept_id == standard_node.id or 
                concept_id in standard_node.children_ids or
                concept_id in standard_node.related_concepts):
                matched_concepts.append(concept_id)
        
        # Identify evidence gaps
        for req_type in standard_node.required_evidence_types:
            if evidence.evidence_type != req_type:
                evidence_gaps.append(f"Missing {req_type.value}")
        
        # Find supporting evidence (conceptual)
        if semantic_score >= 0.7:
            supporting_evidence.append(f"Strong semantic alignment ({semantic_score:.3f})")
        
        if evidence.quality_score >= 0.8:
            supporting_evidence.append(f"High quality evidence ({evidence.quality_score:.3f})")
        
        return matched_concepts, evidence_gaps, supporting_evidence
    
    def _get_domain_embedding_boost(self, evidence: EvidenceDocument, standard_node) -> float:
        """Get domain-specific embedding boost factor."""
        
        if standard_node.domain in evidence.domain_tags:
            return 0.1  # 10% boost for domain alignment
        
        return 0.0
    
    def batch_match_evidence(self, evidence_list: List[EvidenceDocument], 
                           standards: List[str],
                           strategy: MatchingStrategy = MatchingStrategy.EXACT_SEMANTIC) -> Dict[str, List[StandardMatch]]:
        """Batch match multiple evidence documents to standards."""
        
        results = {}
        
        for evidence in evidence_list:
            matches = self.match_evidence_to_standards(evidence, standards, strategy)
            results[evidence.id] = matches
        
        return results
    
    def get_match_analytics(self, matches: List[StandardMatch]) -> Dict[str, Any]:
        """Generate analytics for a set of matches."""
        
        if not matches:
            return {}
        
        confidence_scores = [m.confidence_score for m in matches]
        complexity_counts = {}
        
        for match in matches:
            complexity = match.complexity_level.name
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        return {
            "total_matches": len(matches),
            "avg_confidence": np.mean(confidence_scores),
            "max_confidence": np.max(confidence_scores),
            "min_confidence": np.min(confidence_scores),
            "confidence_std": np.std(confidence_scores),
            "complexity_distribution": complexity_counts,
            "high_confidence_matches": len([m for m in matches if m.confidence_score >= 0.9]),
            "medium_confidence_matches": len([m for m in matches if 0.7 <= m.confidence_score < 0.9]),
            "low_confidence_matches": len([m for m in matches if m.confidence_score < 0.7])
        }
