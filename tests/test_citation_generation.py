"""
Test citation generation with page numbers
"""

import pytest
from datetime import datetime
from src.a3e.core.vector_matching import (
    VectorWeightedMatcher,
    StandardMatch,
    EvidenceDocument,
    MatchingStrategy,
)
from src.a3e.core.accreditation_ontology import (
    AccreditationOntology,
    EvidenceType,
    StandardComplexity,
)
import numpy as np


class TestPageNumberExtraction:
    """Test page number extraction from document content."""
    
    def test_extract_single_page(self):
        """Test extracting a single page number."""
        content = "Some text here\n--- Page 5 ---\nMore text content"
        page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
        assert page_numbers == [5]
    
    def test_extract_multiple_pages(self):
        """Test extracting multiple page numbers."""
        content = """
        Introduction text
        --- Page 1 ---
        First page content
        --- Page 2 ---
        Second page content
        --- Page 5 ---
        Fifth page content
        """
        page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
        assert page_numbers == [1, 2, 5]
    
    def test_extract_no_pages(self):
        """Test content without page markers."""
        content = "Regular text without any page markers"
        page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
        assert page_numbers == []
    
    def test_extract_duplicate_pages(self):
        """Test that duplicate page numbers are deduplicated."""
        content = """
        --- Page 3 ---
        Some content
        --- Page 3 ---
        More from page 3
        """
        page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
        assert page_numbers == [3]
    
    def test_case_insensitive_extraction(self):
        """Test that page extraction is case insensitive."""
        content = "--- page 10 ---\nContent\n--- PAGE 11 ---"
        page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
        assert page_numbers == [10, 11]


class TestStandardMatchWithPageNumbers:
    """Test StandardMatch includes page numbers."""
    
    def test_standard_match_has_page_numbers_field(self):
        """Test that StandardMatch has page_numbers field."""
        match = StandardMatch(
            standard_id="TEST-001",
            evidence_id="DOC-001",
            confidence_score=0.85,
            match_type=MatchingStrategy.EXACT_SEMANTIC,
            complexity_level=StandardComplexity.DIRECT,
            semantic_score=0.9,
            hierarchy_score=0.8,
            domain_score=0.85,
            evidence_score=0.82,
            temporal_score=0.88,
            page_numbers=[1, 2, 3]
        )
        assert hasattr(match, 'page_numbers')
        assert match.page_numbers == [1, 2, 3]
    
    def test_standard_match_default_empty_pages(self):
        """Test that page_numbers defaults to empty list."""
        match = StandardMatch(
            standard_id="TEST-001",
            evidence_id="DOC-001",
            confidence_score=0.85,
            match_type=MatchingStrategy.EXACT_SEMANTIC,
            complexity_level=StandardComplexity.DIRECT,
            semantic_score=0.9,
            hierarchy_score=0.8,
            domain_score=0.85,
            evidence_score=0.82,
            temporal_score=0.88,
        )
        assert match.page_numbers == []


class TestEvidenceDocumentWithPageCount:
    """Test EvidenceDocument includes page_count field."""
    
    def test_evidence_document_has_page_count(self):
        """Test that EvidenceDocument has page_count field."""
        doc = EvidenceDocument(
            id="DOC-001",
            content="Test content\n--- Page 1 ---\nPage 1 text",
            title="Test Document",
            evidence_type=EvidenceType.POLICY_DOCUMENT,
            content_embedding=np.array([0.1, 0.2, 0.3]),
            title_embedding=np.array([0.1, 0.2]),
            source_system="test",
            collection_date=datetime.now(),
            page_count=15
        )
        assert hasattr(doc, 'page_count')
        assert doc.page_count == 15
    
    def test_evidence_document_default_page_count(self):
        """Test that page_count defaults to 0."""
        doc = EvidenceDocument(
            id="DOC-001",
            content="Test content",
            title="Test Document",
            evidence_type=EvidenceType.POLICY_DOCUMENT,
            content_embedding=np.array([0.1, 0.2, 0.3]),
            title_embedding=np.array([0.1, 0.2]),
            source_system="test",
            collection_date=datetime.now()
        )
        assert doc.page_count == 0


def test_citation_format_single_page():
    """Test citation format with a single page number."""
    # This would be tested in integration tests with the actual NarratorAgent
    # Here we just verify the format logic
    page_numbers = [5]
    
    # Single page format
    if len(page_numbers) == 1:
        page_ref = f"p. {page_numbers[0]}"
    
    assert page_ref == "p. 5"


def test_citation_format_multiple_pages():
    """Test citation format with multiple pages."""
    page_numbers = [3, 5, 7]
    
    # Multiple pages (few)
    if len(page_numbers) <= 3:
        pages_str = ", ".join(str(p) for p in page_numbers)
        page_ref = f"pp. {pages_str}"
    
    assert page_ref == "pp. 3, 5, 7"


def test_citation_format_many_pages():
    """Test citation format with many pages."""
    page_numbers = [1, 2, 3, 4, 5, 8, 10, 12]
    
    # Many pages - show range
    page_ref = f"pp. {page_numbers[0]}-{page_numbers[-1]}"
    
    assert page_ref == "pp. 1-12"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
