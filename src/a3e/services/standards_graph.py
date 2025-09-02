"""
StandardsGraph™ - Living standards knowledge graph with multi-granular indexing
Maps accreditor → standard → clause → indicator with semantic embeddings
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


@dataclass
class StandardNode:
    """Node in the standards graph representing a standard/clause/indicator"""
    node_id: str
    accreditor: str
    standard_id: str
    title: str
    description: str
    level: str  # 'standard', 'clause', 'indicator'
    parent_id: Optional[str]
    children: List[str]
    text_content: str
    embedding: Optional[np.ndarray]
    keywords: Set[str]
    version: str
    effective_date: datetime
    evidence_requirements: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'node_id': self.node_id,
            'accreditor': self.accreditor,
            'standard_id': self.standard_id,
            'title': self.title,
            'description': self.description,
            'level': self.level,
            'parent_id': self.parent_id,
            'children': self.children,
            'text_content': self.text_content,
            'keywords': list(self.keywords),
            'version': self.version,
            'effective_date': self.effective_date.isoformat(),
            'evidence_requirements': self.evidence_requirements
        }


class StandardsGraph:
    """Multi-granular knowledge graph of accreditation standards"""
    
    def __init__(self):
        self.nodes: Dict[str, StandardNode] = {}
        self.accreditor_roots: Dict[str, List[str]] = {}
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.keyword_index: Dict[str, Set[str]] = {}  # keyword -> node_ids
        self._initialize_graph()
    
    def _initialize_graph(self):
        """Initialize the graph with comprehensive standards data"""
        # SACSCOC Standards
        self._add_sacscoc_standards()
        # HLC Standards  
        self._add_hlc_standards()
        # MSCHE Standards
        self._add_msche_standards()
        # Additional accreditors
        self._add_wasc_standards()
        self._add_nwccu_standards()
        self._add_neasc_standards()
        
        logger.info(f"StandardsGraph initialized with {len(self.nodes)} nodes")
    
    def _add_sacscoc_standards(self):
        """Add SACSCOC standards to the graph"""
        sacscoc_standards = [
            {
                'id': 'SACSCOC_1',
                'title': 'Institutional Mission',
                'clauses': [
                    {
                        'id': 'SACSCOC_1.1',
                        'title': 'Mission Statement',
                        'description': 'The institution has a clearly defined, comprehensive, and published mission statement',
                        'indicators': [
                            'Mission statement is board-approved',
                            'Mission guides institutional planning',
                            'Mission is publicly available',
                            'Mission reviewed regularly'
                        ]
                    }
                ]
            },
            {
                'id': 'SACSCOC_8',
                'title': 'Faculty',
                'clauses': [
                    {
                        'id': 'SACSCOC_8.1',
                        'title': 'Faculty Qualifications',
                        'description': 'The institution employs competent faculty members qualified to accomplish the mission',
                        'indicators': [
                            'Faculty credentials documented',
                            'Terminal degrees in discipline',
                            'Professional experience relevant',
                            'Ongoing professional development'
                        ]
                    },
                    {
                        'id': 'SACSCOC_8.2a',
                        'title': 'Faculty Evaluation',
                        'description': 'The institution regularly evaluates the effectiveness of each faculty member',
                        'indicators': [
                            'Annual performance reviews',
                            'Student evaluation data',
                            'Peer review process',
                            'Professional development plans'
                        ]
                    }
                ]
            },
            {
                'id': 'SACSCOC_10',
                'title': 'Financial Resources',
                'clauses': [
                    {
                        'id': 'SACSCOC_10.1',
                        'title': 'Financial Stability',
                        'description': 'The institution provides evidence of adequate financial resources',
                        'indicators': [
                            'Positive net assets',
                            'Adequate cash reserves',
                            'Diversified revenue streams',
                            'Clean audit opinions'
                        ]
                    }
                ]
            }
        ]
        
        for standard in sacscoc_standards:
            # Create standard node
            standard_node = StandardNode(
                node_id=standard['id'],
                accreditor='SACSCOC',
                standard_id=standard['id'],
                title=standard['title'],
                description=f"SACSCOC Standard: {standard['title']}",
                level='standard',
                parent_id=None,
                children=[],
                text_content=standard['title'],
                embedding=None,
                keywords=self._extract_keywords(standard['title']),
                version='2024',
                effective_date=datetime(2024, 1, 1),
                evidence_requirements=[]
            )
            self.nodes[standard_node.node_id] = standard_node
            self.accreditor_roots.setdefault('SACSCOC', []).append(standard_node.node_id)
            
            # Add clauses
            for clause in standard.get('clauses', []):
                clause_node = StandardNode(
                    node_id=clause['id'],
                    accreditor='SACSCOC',
                    standard_id=clause['id'],
                    title=clause['title'],
                    description=clause['description'],
                    level='clause',
                    parent_id=standard['id'],
                    children=[],
                    text_content=f"{clause['title']}: {clause['description']}",
                    embedding=None,
                    keywords=self._extract_keywords(f"{clause['title']} {clause['description']}"),
                    version='2024',
                    effective_date=datetime(2024, 1, 1),
                    evidence_requirements=clause.get('indicators', [])
                )
                self.nodes[clause_node.node_id] = clause_node
                standard_node.children.append(clause_node.node_id)
                
                # Add indicators
                for idx, indicator in enumerate(clause.get('indicators', [])):
                    indicator_id = f"{clause['id']}_ind_{idx+1}"
                    indicator_node = StandardNode(
                        node_id=indicator_id,
                        accreditor='SACSCOC',
                        standard_id=indicator_id,
                        title=f"Indicator {idx+1}",
                        description=indicator,
                        level='indicator',
                        parent_id=clause['id'],
                        children=[],
                        text_content=indicator,
                        embedding=None,
                        keywords=self._extract_keywords(indicator),
                        version='2024',
                        effective_date=datetime(2024, 1, 1),
                        evidence_requirements=[indicator]
                    )
                    self.nodes[indicator_id] = indicator_node
                    clause_node.children.append(indicator_id)
    
    def _add_hlc_standards(self):
        """Add HLC Criteria to the graph"""
        hlc_standards = [
            {
                'id': 'HLC_1',
                'title': 'Mission',
                'clauses': [
                    {
                        'id': 'HLC_1.A',
                        'title': 'Mission Articulation',
                        'description': 'The institution\'s mission is articulated publicly',
                        'indicators': [
                            'Mission documents are current',
                            'Mission guides operations',
                            'Mission understood by stakeholders'
                        ]
                    },
                    {
                        'id': 'HLC_1.B',
                        'title': 'Mission and Public Good',
                        'description': 'The mission articulates commitment to the public good',
                        'indicators': [
                            'Community engagement documented',
                            'Public service initiatives',
                            'Economic development contributions'
                        ]
                    }
                ]
            },
            {
                'id': 'HLC_3',
                'title': 'Teaching and Learning',
                'clauses': [
                    {
                        'id': 'HLC_3.A',
                        'title': 'Degree Program Quality',
                        'description': 'Degree programs appropriate to higher education',
                        'indicators': [
                            'Rigor appropriate to degree level',
                            'Differentiated learning goals',
                            'Program assessment processes'
                        ]
                    }
                ]
            }
        ]
        
        for standard in hlc_standards:
            self._add_standard_hierarchy('HLC', standard)
    
    def _add_msche_standards(self):
        """Add MSCHE Standards to the graph"""
        msche_standards = [
            {
                'id': 'MSCHE_I',
                'title': 'Mission and Goals',
                'clauses': [
                    {
                        'id': 'MSCHE_I.1',
                        'title': 'Clearly Defined Mission',
                        'description': 'Clearly defined mission and goals that guide operations',
                        'indicators': [
                            'Mission approved by governing body',
                            'Goals measurable and achievable',
                            'Regular mission review process'
                        ]
                    }
                ]
            },
            {
                'id': 'MSCHE_V',
                'title': 'Educational Effectiveness Assessment',
                'clauses': [
                    {
                        'id': 'MSCHE_V.1',
                        'title': 'Assessment of Student Learning',
                        'description': 'Clearly stated learning outcomes with assessment',
                        'indicators': [
                            'Organized assessment process',
                            'Direct measures of learning',
                            'Assessment results used for improvement'
                        ]
                    }
                ]
            }
        ]
        
        for standard in msche_standards:
            self._add_standard_hierarchy('MSCHE', standard)
    
    def _add_wasc_standards(self):
        """Add WASC Standards"""
        wasc_standards = [
            {
                'id': 'WASC_1',
                'title': 'Defining Institutional Purposes',
                'clauses': [
                    {
                        'id': 'WASC_1.1',
                        'title': 'Institutional Purposes',
                        'description': 'The institution\'s purposes are appropriate and clear',
                        'indicators': ['Educational objectives defined', 'Purpose drives planning']
                    }
                ]
            }
        ]
        for standard in wasc_standards:
            self._add_standard_hierarchy('WASC', standard)
    
    def _add_nwccu_standards(self):
        """Add NWCCU Standards"""
        nwccu_standards = [
            {
                'id': 'NWCCU_1',
                'title': 'Mission and Core Themes',
                'clauses': [
                    {
                        'id': 'NWCCU_1.A',
                        'title': 'Mission',
                        'description': 'The institution has a widely published mission statement',
                        'indicators': ['Mission defines purpose', 'Core themes identified']
                    }
                ]
            }
        ]
        for standard in nwccu_standards:
            self._add_standard_hierarchy('NWCCU', standard)
    
    def _add_neasc_standards(self):
        """Add NEASC Standards"""
        neasc_standards = [
            {
                'id': 'NEASC_1',
                'title': 'Mission and Purposes',
                'clauses': [
                    {
                        'id': 'NEASC_1.1',
                        'title': 'Mission Statement',
                        'description': 'The institution has a mission appropriate to higher education',
                        'indicators': ['Mission defines educational purpose', 'Mission widely disseminated']
                    }
                ]
            }
        ]
        for standard in neasc_standards:
            self._add_standard_hierarchy('NEASC', standard)
    
    def _add_standard_hierarchy(self, accreditor: str, standard_data: Dict[str, Any]):
        """Helper to add a standard and its hierarchy to the graph"""
        # Create standard node
        standard_node = StandardNode(
            node_id=standard_data['id'],
            accreditor=accreditor,
            standard_id=standard_data['id'],
            title=standard_data['title'],
            description=f"{accreditor} Standard: {standard_data['title']}",
            level='standard',
            parent_id=None,
            children=[],
            text_content=standard_data['title'],
            embedding=None,
            keywords=self._extract_keywords(standard_data['title']),
            version='2024',
            effective_date=datetime(2024, 1, 1),
            evidence_requirements=[]
        )
        self.nodes[standard_node.node_id] = standard_node
        self.accreditor_roots.setdefault(accreditor, []).append(standard_node.node_id)
        
        # Add clauses and indicators
        for clause in standard_data.get('clauses', []):
            clause_node = StandardNode(
                node_id=clause['id'],
                accreditor=accreditor,
                standard_id=clause['id'],
                title=clause['title'],
                description=clause['description'],
                level='clause',
                parent_id=standard_data['id'],
                children=[],
                text_content=f"{clause['title']}: {clause['description']}",
                embedding=None,
                keywords=self._extract_keywords(f"{clause['title']} {clause['description']}"),
                version='2024',
                effective_date=datetime(2024, 1, 1),
                evidence_requirements=clause.get('indicators', [])
            )
            self.nodes[clause_node.node_id] = clause_node
            standard_node.children.append(clause_node.node_id)
            
            # Add indicators
            for idx, indicator in enumerate(clause.get('indicators', [])):
                indicator_id = f"{clause['id']}_ind_{idx+1}"
                indicator_node = StandardNode(
                    node_id=indicator_id,
                    accreditor=accreditor,
                    standard_id=indicator_id,
                    title=f"Indicator {idx+1}",
                    description=indicator,
                    level='indicator',
                    parent_id=clause['id'],
                    children=[],
                    text_content=indicator,
                    embedding=None,
                    keywords=self._extract_keywords(indicator),
                    version='2024',
                    effective_date=datetime(2024, 1, 1),
                    evidence_requirements=[indicator]
                )
                self.nodes[indicator_id] = indicator_node
                clause_node.children.append(indicator_id)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text for sparse retrieval"""
        # Simple keyword extraction - in production would use NLP
        import re
        words = re.findall(r'\b[a-z]+\b', text.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'has', 'have', 'had'}
        keywords = {w for w in words if len(w) > 3 and w not in stopwords}
        
        # Update keyword index
        for keyword in keywords:
            self.keyword_index.setdefault(keyword, set())
        
        return keywords
    
    def get_node(self, node_id: str) -> Optional[StandardNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_accreditor_standards(self, accreditor: str) -> List[StandardNode]:
        """Get all standards for an accreditor"""
        root_ids = self.accreditor_roots.get(accreditor, [])
        standards = []
        for root_id in root_ids:
            node = self.nodes.get(root_id)
            if node:
                standards.append(node)
        return standards
    
    def get_children(self, node_id: str) -> List[StandardNode]:
        """Get all children of a node"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children if child_id in self.nodes]
    
    def get_path_to_root(self, node_id: str) -> List[StandardNode]:
        """Get the path from a node to the root"""
        path = []
        current_id = node_id
        while current_id:
            node = self.nodes.get(current_id)
            if not node:
                break
            path.append(node)
            current_id = node.parent_id
        return list(reversed(path))
    
    def search_by_keywords(self, keywords: Set[str], limit: int = 10) -> List[Tuple[StandardNode, float]]:
        """Search nodes by keywords with relevance scoring"""
        scores = {}
        for keyword in keywords:
            if keyword in self.keyword_index:
                for node_id in self.keyword_index[keyword]:
                    scores[node_id] = scores.get(node_id, 0) + 1
        
        # Normalize scores and sort
        results = []
        for node_id, score in scores.items():
            node = self.nodes.get(node_id)
            if node:
                normalized_score = score / len(keywords)
                results.append((node, normalized_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def export_graph_structure(self) -> Dict[str, Any]:
        """Export the graph structure for visualization"""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'accreditors': list(self.accreditor_roots.keys()),
            'total_nodes': len(self.nodes),
            'by_level': {
                'standards': len([n for n in self.nodes.values() if n.level == 'standard']),
                'clauses': len([n for n in self.nodes.values() if n.level == 'clause']),
                'indicators': len([n for n in self.nodes.values() if n.level == 'indicator'])
            }
        }


# Global instance
standards_graph = StandardsGraph()