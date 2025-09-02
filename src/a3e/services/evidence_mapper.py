"""
EvidenceMapper™ - Multi-stage evidence to standards mapping with confidence scoring
Dual-encoder retrieval + cross-encoder reranking + explanation extraction
"""

import hashlib
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from .standards_graph import standards_graph, StandardNode

logger = logging.getLogger(__name__)


@dataclass
class MappingResult:
    """Result of mapping evidence to a standard"""
    standard_id: str
    confidence: float  # 0-1 calibrated confidence score
    rationale_spans: List[str]  # Extracted text spans supporting the mapping
    explanation: str  # Human-readable explanation
    accreditor: str
    standard_title: str
    match_type: str  # 'exact', 'strong', 'partial', 'weak'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'standard_id': self.standard_id,
            'confidence': round(self.confidence, 3),
            'rationale_spans': self.rationale_spans,
            'explanation': self.explanation,
            'accreditor': self.accreditor,
            'standard_title': self.standard_title,
            'match_type': self.match_type
        }


@dataclass
class EvidenceDocument:
    """Document to be mapped to standards"""
    doc_id: str
    text: str
    metadata: Dict[str, Any]
    doc_type: str  # 'policy', 'syllabus', 'assessment', 'report', etc.
    source_system: Optional[str]  # 'manual', 'lms', 'erp', etc.
    upload_date: datetime
    
    def get_fingerprint(self) -> str:
        """Generate content fingerprint for deduplication"""
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]


class EvidenceMapper:
    """Maps evidence documents to accreditation standards with confidence scoring"""
    
    def __init__(self):
        self.graph = standards_graph
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2,
            stop_words='english'
        )
        self.corpus_embeddings = {}
        self.calibration_params = {
            'temperature': 1.5,  # For confidence calibration
            'threshold_exact': 0.85,
            'threshold_strong': 0.70,
            'threshold_partial': 0.50,
            'threshold_weak': 0.30
        }
        self._build_corpus_index()
    
    def _build_corpus_index(self):
        """Build TF-IDF index of all standards for fast retrieval"""
        corpus = []
        node_ids = []
        
        for node_id, node in self.graph.nodes.items():
            # Combine all text for the node
            full_text = f"{node.title} {node.description} {node.text_content}"
            if node.evidence_requirements:
                full_text += " " + " ".join(node.evidence_requirements)
            corpus.append(full_text)
            node_ids.append(node_id)
        
        if corpus:
            self.corpus_matrix = self.vectorizer.fit_transform(corpus)
            self.corpus_node_ids = node_ids
            logger.info(f"Built corpus index with {len(corpus)} standards")
    
    def map_evidence(
        self,
        document: EvidenceDocument,
        top_k: int = 10,
        min_confidence: float = 0.3
    ) -> List[MappingResult]:
        """
        Map evidence document to standards with multi-stage pipeline
        
        Step 1: Fast candidate retrieval (dual-encoder)
        Step 2: Cross-encoder reranking
        Step 3: Confidence calibration
        Step 4: Rationale extraction
        """
        
        # Step 1: Retrieve top-K candidates via vector search
        candidates = self._retrieve_candidates(document.text, top_k * 2)
        
        # Step 2: Cross-encode and rerank
        reranked = self._cross_encode_rerank(document.text, candidates)
        
        # Step 3: Calibrate confidence scores
        calibrated = self._calibrate_confidence(reranked)
        
        # Step 4: Extract rationales and generate explanations
        results = []
        for node_id, raw_score, calibrated_score in calibrated[:top_k]:
            if calibrated_score < min_confidence:
                continue
            
            node = self.graph.get_node(node_id)
            if not node:
                continue
            
            rationale_spans = self._extract_rationale_spans(document.text, node)
            explanation = self._generate_explanation(document, node, rationale_spans, calibrated_score)
            match_type = self._classify_match_type(calibrated_score)
            
            results.append(MappingResult(
                standard_id=node.standard_id,
                confidence=calibrated_score,
                rationale_spans=rationale_spans,
                explanation=explanation,
                accreditor=node.accreditor,
                standard_title=node.title,
                match_type=match_type
            ))
        
        return results
    
    def _retrieve_candidates(self, query_text: str, top_k: int) -> List[Tuple[str, float]]:
        """Fast candidate retrieval using TF-IDF similarity"""
        if not hasattr(self, 'corpus_matrix'):
            return []
        
        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.corpus_matrix).flatten()
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        candidates = []
        for idx in top_indices:
            if similarities[idx] > 0:
                candidates.append((self.corpus_node_ids[idx], float(similarities[idx])))
        
        return candidates
    
    def _cross_encode_rerank(
        self,
        doc_text: str,
        candidates: List[Tuple[str, float]]
    ) -> List[Tuple[str, float, float]]:
        """Cross-encoder reranking for precision"""
        reranked = []
        
        for node_id, retrieval_score in candidates:
            node = self.graph.get_node(node_id)
            if not node:
                continue
            
            # Compute detailed similarity features
            features = self._extract_matching_features(doc_text, node)
            
            # Combine features into cross-encoder score
            cross_score = self._compute_cross_encoder_score(features)
            
            # Combine retrieval and cross-encoder scores
            combined_score = 0.3 * retrieval_score + 0.7 * cross_score
            
            reranked.append((node_id, retrieval_score, combined_score))
        
        # Sort by combined score
        reranked.sort(key=lambda x: x[2], reverse=True)
        return reranked
    
    def _extract_matching_features(self, doc_text: str, node: StandardNode) -> Dict[str, float]:
        """Extract detailed matching features for cross-encoder"""
        doc_lower = doc_text.lower()
        node_text_lower = f"{node.title} {node.description}".lower()
        
        features = {
            'title_overlap': self._compute_word_overlap(doc_lower, node.title.lower()),
            'desc_overlap': self._compute_word_overlap(doc_lower, node.description.lower()),
            'keyword_match': len(node.keywords.intersection(self._extract_keywords(doc_text))) / max(len(node.keywords), 1),
            'evidence_req_match': 0.0,
            'length_ratio': min(len(doc_text), len(node_text_lower)) / max(len(doc_text), len(node_text_lower))
        }
        
        # Check evidence requirements matching
        if node.evidence_requirements:
            req_matches = sum(1 for req in node.evidence_requirements if any(word in doc_lower for word in req.lower().split()))
            features['evidence_req_match'] = req_matches / len(node.evidence_requirements)
        
        return features
    
    def _compute_word_overlap(self, text1: str, text2: str) -> float:
        """Compute word overlap between two texts"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words2:
            return 0.0
        return len(words1.intersection(words2)) / len(words2)
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text"""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        return {w for w in words if len(w) > 3 and w not in stopwords}
    
    def _compute_cross_encoder_score(self, features: Dict[str, float]) -> float:
        """Compute cross-encoder score from features"""
        # Weighted combination of features
        weights = {
            'title_overlap': 0.25,
            'desc_overlap': 0.20,
            'keyword_match': 0.25,
            'evidence_req_match': 0.25,
            'length_ratio': 0.05
        }
        
        score = sum(features.get(k, 0) * w for k, w in weights.items())
        return min(1.0, score)
    
    def _calibrate_confidence(
        self,
        scores: List[Tuple[str, float, float]]
    ) -> List[Tuple[str, float, float]]:
        """Calibrate raw scores to confidence probabilities"""
        if not scores:
            return []
        
        # Apply temperature scaling for calibration
        temperature = self.calibration_params['temperature']
        
        calibrated = []
        for node_id, raw_score, combined_score in scores:
            # Apply sigmoid with temperature
            calibrated_score = 1 / (1 + np.exp(-combined_score * 10 / temperature))
            calibrated.append((node_id, raw_score, calibrated_score))
        
        return calibrated
    
    def _extract_rationale_spans(self, doc_text: str, node: StandardNode, max_spans: int = 3) -> List[str]:
        """Extract text spans from document that support the mapping"""
        spans = []
        sentences = re.split(r'[.!?]+', doc_text)
        
        # Score each sentence for relevance to the standard
        scored_sentences = []
        for sentence in sentences:
            if len(sentence.strip()) < 20:
                continue
            
            score = 0
            sentence_lower = sentence.lower()
            
            # Check for keyword matches
            for keyword in node.keywords:
                if keyword in sentence_lower:
                    score += 1
            
            # Check for evidence requirement matches
            for req in node.evidence_requirements:
                req_words = set(req.lower().split())
                sentence_words = set(sentence_lower.split())
                overlap = len(req_words.intersection(sentence_words))
                score += overlap / max(len(req_words), 1)
            
            if score > 0:
                scored_sentences.append((sentence.strip(), score))
        
        # Sort by score and take top spans
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        for sentence, score in scored_sentences[:max_spans]:
            # Highlight matching keywords in the span
            highlighted = sentence
            for keyword in node.keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                highlighted = pattern.sub(f"**{keyword}**", highlighted)
            spans.append(highlighted)
        
        return spans
    
    def _generate_explanation(
        self,
        document: EvidenceDocument,
        node: StandardNode,
        rationale_spans: List[str],
        confidence: float
    ) -> str:
        """Generate human-readable explanation for the mapping"""
        match_type = self._classify_match_type(confidence)
        
        explanation_parts = [
            f"This {document.doc_type} document {match_type} matches {node.accreditor} {node.standard_id}: {node.title}."
        ]
        
        if rationale_spans:
            explanation_parts.append(f"Key evidence found: {len(rationale_spans)} relevant passages identified.")
        
        if node.evidence_requirements:
            matched_reqs = []
            doc_lower = document.text.lower()
            for req in node.evidence_requirements[:3]:
                if any(word in doc_lower for word in req.lower().split()):
                    matched_reqs.append(req)
            
            if matched_reqs:
                explanation_parts.append(f"Addresses requirements: {', '.join(matched_reqs[:2])}")
        
        explanation_parts.append(f"Confidence: {confidence:.1%}")
        
        return " ".join(explanation_parts)
    
    def _classify_match_type(self, confidence: float) -> str:
        """Classify the match type based on confidence score"""
        thresholds = self.calibration_params
        
        if confidence >= thresholds['threshold_exact']:
            return 'exactly'
        elif confidence >= thresholds['threshold_strong']:
            return 'strongly'
        elif confidence >= thresholds['threshold_partial']:
            return 'partially'
        elif confidence >= thresholds['threshold_weak']:
            return 'weakly'
        else:
            return 'minimally'
    
    def batch_map_evidence(
        self,
        documents: List[EvidenceDocument],
        top_k: int = 5
    ) -> Dict[str, List[MappingResult]]:
        """Batch process multiple documents"""
        results = {}
        for doc in documents:
            mappings = self.map_evidence(doc, top_k=top_k)
            results[doc.doc_id] = mappings
        return results
    
    def get_mapping_statistics(self, mappings: List[MappingResult]) -> Dict[str, Any]:
        """Generate statistics for a set of mappings"""
        if not mappings:
            return {'total': 0}
        
        stats = {
            'total': len(mappings),
            'avg_confidence': np.mean([m.confidence for m in mappings]),
            'by_accreditor': {},
            'by_match_type': {},
            'high_confidence_count': sum(1 for m in mappings if m.confidence >= 0.7),
            'with_rationales': sum(1 for m in mappings if m.rationale_spans)
        }
        
        for mapping in mappings:
            stats['by_accreditor'][mapping.accreditor] = stats['by_accreditor'].get(mapping.accreditor, 0) + 1
            stats['by_match_type'][mapping.match_type] = stats['by_match_type'].get(mapping.match_type, 0) + 1
        
        return stats


# Global instance
evidence_mapper = EvidenceMapper()