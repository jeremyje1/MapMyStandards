"""
StandardsGraph™ - Living standards knowledge graph with multi-granular indexing
Maps accreditor → standard → clause → indicator with sparse keyword search
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StandardNode:
    node_id: str
    accreditor: str
    standard_id: str
    title: str
    description: str
    level: str  # 'standard', 'clause', 'indicator'
    parent_id: Optional[str]
    children: List[str]
    text_content: str
    keywords: Set[str]
    version: str
    effective_date: datetime
    evidence_requirements: List[str]

    def to_dict(self) -> Dict[str, Any]:
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
            'evidence_requirements': self.evidence_requirements,
        }


class StandardsGraph:
    """Multi-granular knowledge graph of accreditation standards."""

    def __init__(self) -> None:
        self.nodes: Dict[str, StandardNode] = {}
        self.accreditor_roots: Dict[str, List[str]] = {}
        self.keyword_index: Dict[str, Set[str]] = {}
        self._initialize_graph()

    # ------------------------ Initialization ------------------------
    def _initialize_graph(self) -> None:
        self._add_sacscoc_standards()
        self._add_hlc_standards()
        self._add_msche_standards()
        self._add_wasc_standards()
        self._add_nwccu_standards()
        self._add_neasc_standards()
        logger.info("StandardsGraph initialized with %d nodes", len(self.nodes))

    # ------------------------ Data seeding ------------------------
    def _add_sacscoc_standards(self) -> None:
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
                            'Mission reviewed regularly',
                        ],
                    }
                ],
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
                            'Ongoing professional development',
                        ],
                    },
                    {
                        'id': 'SACSCOC_8.2a',
                        'title': 'Faculty Evaluation',
                        'description': 'The institution regularly evaluates the effectiveness of each faculty member',
                        'indicators': [
                            'Annual performance reviews',
                            'Student evaluation data',
                            'Peer review process',
                            'Professional development plans',
                        ],
                    },
                ],
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
                            'Clean audit opinions',
                        ],
                    }
                ],
            },
        ]
        for standard in sacscoc_standards:
            self._add_standard_hierarchy('SACSCOC', standard)

    def _add_hlc_standards(self) -> None:
        hlc_standards = [
            {
                'id': 'HLC_1',
                'title': 'Mission',
                'clauses': [
                    {
                        'id': 'HLC_1.A',
                        'title': 'Mission Articulation',
                        'description': "The institution's mission is articulated publicly",
                        'indicators': [
                            'Mission documents are current',
                            'Mission guides operations',
                            'Mission understood by stakeholders',
                        ],
                    },
                    {
                        'id': 'HLC_1.B',
                        'title': 'Mission and Public Good',
                        'description': 'The mission articulates commitment to the public good',
                        'indicators': [
                            'Community engagement documented',
                            'Public service initiatives',
                            'Economic development contributions',
                        ],
                    },
                ],
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
                            'Program assessment processes',
                        ],
                    }
                ],
            },
        ]
        for standard in hlc_standards:
            self._add_standard_hierarchy('HLC', standard)

    def _add_msche_standards(self) -> None:
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
                            'Regular mission review process',
                        ],
                    }
                ],
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
                            'Assessment results used for improvement',
                        ],
                    }
                ],
            },
        ]
        for standard in msche_standards:
            self._add_standard_hierarchy('MSCHE', standard)

    def _add_wasc_standards(self) -> None:
        wasc_standards = [
            {
                'id': 'WASC_1',
                'title': 'Defining Institutional Purposes',
                'clauses': [
                    {
                        'id': 'WASC_1.1',
                        'title': 'Institutional Purposes',
                        'description': "The institution's purposes are appropriate and clear",
                        'indicators': ['Educational objectives defined', 'Purpose drives planning'],
                    }
                ],
            }
        ]
        for standard in wasc_standards:
            self._add_standard_hierarchy('WASC', standard)

    def _add_nwccu_standards(self) -> None:
        nwccu_standards = [
            {
                'id': 'NWCCU_1',
                'title': 'Mission and Core Themes',
                'clauses': [
                    {
                        'id': 'NWCCU_1.A',
                        'title': 'Mission',
                        'description': 'The institution has a widely published mission statement',
                        'indicators': ['Mission defines purpose', 'Core themes identified'],
                    }
                ],
            }
        ]
        for standard in nwccu_standards:
            self._add_standard_hierarchy('NWCCU', standard)

    def _add_neasc_standards(self) -> None:
        neasc_standards = [
            {
                'id': 'NEASC_1',
                'title': 'Mission and Purposes',
                'clauses': [
                    {
                        'id': 'NEASC_1.1',
                        'title': 'Mission Statement',
                        'description': 'The institution has a mission appropriate to higher education',
                        'indicators': ['Mission defines educational purpose', 'Mission widely disseminated'],
                    }
                ],
            }
        ]
        for standard in neasc_standards:
            self._add_standard_hierarchy('NEASC', standard)

    # ------------------------ Helpers ------------------------
    def _add_standard_hierarchy(self, accreditor: str, standard_data: Dict[str, Any]) -> None:
        # Standard node
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
            keywords=self._extract_keywords(standard_data['title']),
            version='2024',
            effective_date=datetime(2024, 1, 1),
            evidence_requirements=[],
        )
        self.nodes[standard_node.node_id] = standard_node
        self.accreditor_roots.setdefault(accreditor, []).append(standard_node.node_id)
        self._index_node_keywords(standard_node)

        # Clauses
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
                keywords=self._extract_keywords(f"{clause['title']} {clause['description']}"),
                version='2024',
                effective_date=datetime(2024, 1, 1),
                evidence_requirements=clause.get('indicators', []),
            )
            self.nodes[clause_node.node_id] = clause_node
            standard_node.children.append(clause_node.node_id)
            self._index_node_keywords(clause_node)

            # Indicators
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
                    keywords=self._extract_keywords(indicator),
                    version='2024',
                    effective_date=datetime(2024, 1, 1),
                    evidence_requirements=[indicator],
                )
                self.nodes[indicator_id] = indicator_node
                clause_node.children.append(indicator_id)
                self._index_node_keywords(indicator_node)

    # ------------------------ Keyword indexing/search ------------------------
    def _extract_keywords(self, text: str) -> Set[str]:
        import re
        words = re.findall(r"\b[a-z]+\b", (text or '').lower())
        stop = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'has', 'have', 'had'
        }
        return {w for w in words if len(w) > 3 and w not in stop}

    def _index_node_keywords(self, node: StandardNode) -> None:
        for kw in node.keywords:
            self.keyword_index.setdefault(kw, set()).add(node.node_id)

    def search_by_keywords(self, keywords: Set[str], limit: int = 10) -> List[Tuple[StandardNode, float]]:
        scores: Dict[str, int] = {}
        for kw in keywords:
            for node_id in self.keyword_index.get(kw, set()):
                scores[node_id] = scores.get(node_id, 0) + 1
        results: List[Tuple[StandardNode, float]] = []
        total = float(len(keywords) or 1)
        for node_id, sc in scores.items():
            node = self.nodes.get(node_id)
            if node:
                results.append((node, sc / total))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    # ------------------------ Traversal ------------------------
    def get_node(self, node_id: str) -> Optional[StandardNode]:
        return self.nodes.get(node_id)

    def get_accreditor_standards(self, accreditor: str) -> List[StandardNode]:
        root_ids = self.accreditor_roots.get(accreditor, [])
        return [self.nodes[r] for r in root_ids if r in self.nodes]

    def get_nodes_by_accreditor(self, accreditor: str, levels: Optional[Set[str]] = None) -> List[StandardNode]:
        if levels is None:
            levels = {'standard', 'clause', 'indicator'}
        return [n for n in self.nodes.values() if n.accreditor == accreditor and n.level in levels]

    def get_children(self, node_id: str) -> List[StandardNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[c] for c in node.children if c in self.nodes]

    def get_path_to_root(self, node_id: str) -> List[StandardNode]:
        path: List[StandardNode] = []
        current = self.nodes.get(node_id)
        while current:
            path.append(current)
            current = self.nodes.get(current.parent_id) if current.parent_id else None
        return list(reversed(path))

    # ------------------------ Cross-accreditor matching ------------------------
    def _jaccard(self, a: Set[str], b: Set[str]) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return float(inter) / float(union) if union else 0.0

    def find_cross_accreditor_matches(self, source: str, target: str, threshold: float = 0.3, top_k: int = 3) -> List[Dict[str, Any]]:
        src_nodes = [n for n in self.get_nodes_by_accreditor(source, {'standard'})]
        tgt_nodes = [n for n in self.get_nodes_by_accreditor(target, {'standard'})]

        def kwset(node: StandardNode) -> Set[str]:
            base = set(node.keywords)
            base |= self._extract_keywords(node.title or '')
            base |= self._extract_keywords(node.description or '')
            return base

        tgt_kw = [(t, kwset(t)) for t in tgt_nodes]
        results: List[Dict[str, Any]] = []
        for s in src_nodes:
            s_kw = kwset(s)
            scored: List[Tuple[StandardNode, float]] = []
            for (t, tkw) in tgt_kw:
                sc = self._jaccard(s_kw, tkw)
                if sc >= threshold:
                    scored.append((t, sc))
            scored.sort(key=lambda x: x[1], reverse=True)
            for t, sc in scored[:max(1, top_k)]:
                results.append({
                    'source_id': s.node_id,
                    'source_title': s.title,
                    'target_id': t.node_id,
                    'target_title': t.title,
                    'score': round(float(sc), 3),
                })
        results.sort(key=lambda d: d['score'], reverse=True)
        return results

    # ------------------------ Stats/Export ------------------------
    def get_graph_stats(self) -> Dict[str, Any]:
        total_edges = sum(len(n.children) for n in self.nodes.values())
        return {
            'total_nodes': len(self.nodes),
            'total_edges': total_edges,
            'accreditors': list(self.accreditor_roots.keys()),
            'by_level': {
                'standards': len([n for n in self.nodes.values() if n.level == 'standard']),
                'clauses': len([n for n in self.nodes.values() if n.level == 'clause']),
                'indicators': len([n for n in self.nodes.values() if n.level == 'indicator']),
            },
        }

    def export_graph_structure(self) -> Dict[str, Any]:
        return {
            'nodes': [n.to_dict() for n in self.nodes.values()],
            'accreditors': list(self.accreditor_roots.keys()),
            'total_nodes': len(self.nodes),
            'by_level': {
                'standards': len([n for n in self.nodes.values() if n.level == 'standard']),
                'clauses': len([n for n in self.nodes.values() if n.level == 'clause']),
                'indicators': len([n for n in self.nodes.values() if n.level == 'indicator']),
            },
        }


# Global instance
standards_graph = StandardsGraph()
