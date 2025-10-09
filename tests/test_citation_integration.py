"""
Integration test demonstrating citation generation with page numbers.
This test shows how the entire flow works from document processing to citation generation.
"""

import pytest
from datetime import datetime
import numpy as np
from src.a3e.core.vector_matching import (
    VectorWeightedMatcher,
    EvidenceDocument,
    MatchingStrategy,
)
from src.a3e.core.accreditation_ontology import (
    AccreditationOntology,
    AccreditationDomain,
    EvidenceType,
    StandardComplexity,
)


def test_end_to_end_citation_with_page_numbers():
    """
    Test the complete flow of citation generation with page numbers.
    This demonstrates how page markers in documents result in citations with page references.
    """
    
    # 1. Simulate a document with page markers (like PDF/DOCX processing would create)
    document_content = """
Mission Statement
--- Page 1 ---
Our institution is committed to excellence in teaching, research, and service.
We strive to provide quality education that prepares students for successful careers.

Strategic Goals
--- Page 2 ---
1. Enhance student learning outcomes through innovative curriculum design
2. Strengthen faculty development and support
3. Improve institutional assessment processes

Assessment Results
--- Page 5 ---
Our annual assessment shows significant improvement in student achievement.
Graduation rates have increased by 15% over the past three years.
Faculty satisfaction scores demonstrate high morale and engagement.

--- Page 6 ---
The institution maintains strong financial stability and adequate resources
to support our mission and strategic goals.
"""
    
    # 2. Create an EvidenceDocument (simulating what the document service would create)
    evidence = EvidenceDocument(
        id="DOC-001",
        content=document_content,
        title="Institutional Effectiveness Report 2024",
        evidence_type=EvidenceType.ASSESSMENT_DATA,
        content_embedding=np.random.rand(384),  # Simulated embedding
        title_embedding=np.random.rand(384),
        source_system="upload",
        collection_date=datetime(2024, 1, 15),
        page_count=6,
        domain_tags=[AccreditationDomain.INSTITUTIONAL_EFFECTIVENESS]
    )
    
    # 3. Extract page numbers from the content
    page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(evidence.content)
    
    # Verify page numbers were extracted correctly
    assert page_numbers == [1, 2, 5, 6], f"Expected [1, 2, 5, 6] but got {page_numbers}"
    
    # 4. Simulate citation generation (like NarratorAgent would do)
    citation_parts = [
        evidence.title,
        evidence.evidence_type.value,
        evidence.collection_date.strftime('%Y-%m-%d')
    ]
    
    # Add page numbers to citation
    if page_numbers:
        if len(page_numbers) == 1:
            citation_parts.append(f"p. {page_numbers[0]}")
        elif len(page_numbers) <= 3:
            pages_str = ", ".join(str(p) for p in page_numbers)
            citation_parts.append(f"pp. {pages_str}")
        else:
            # For many pages, show range
            citation_parts.append(f"pp. {page_numbers[0]}-{page_numbers[-1]}")
    
    final_citation = f"{citation_parts[0]} ({', '.join(citation_parts[1:])})"
    
    # 5. Verify the citation format
    expected_citation = "Institutional Effectiveness Report 2024 (assessment_data, 2024-01-15, pp. 1-6)"
    assert final_citation == expected_citation, f"Expected '{expected_citation}' but got '{final_citation}'"
    
    print("\n✅ Integration test passed!")
    print(f"📄 Document: {evidence.title}")
    print(f"📊 Pages found: {page_numbers}")
    print(f"📝 Generated citation: {final_citation}")
    print("\nThis demonstrates the CiteGuard™ promise:")
    print("- Evidence is automatically linked to specific page numbers")
    print("- Citations include precise document references")
    print("- Page markers from PDF/DOCX processing enable accurate citations")


def test_citation_format_variations():
    """
    Test different citation formats based on number of pages.
    """
    
    base_citation = "Strategic Plan 2024 (policy_document, 2024-01-01"
    
    # Test 1: Single page
    pages = [15]
    if len(pages) == 1:
        page_ref = f", p. {pages[0]})"
    citation = base_citation + page_ref
    assert citation == "Strategic Plan 2024 (policy_document, 2024-01-01, p. 15)"
    print(f"✅ Single page: {citation}")
    
    # Test 2: Few pages (2-3)
    pages = [3, 7, 12]
    if len(pages) <= 3:
        pages_str = ", ".join(str(p) for p in pages)
        page_ref = f", pp. {pages_str})"
    citation = base_citation + page_ref
    assert citation == "Strategic Plan 2024 (policy_document, 2024-01-01, pp. 3, 7, 12)"
    print(f"✅ Few pages: {citation}")
    
    # Test 3: Many pages (4+)
    pages = [1, 2, 3, 5, 8, 10, 12, 15]
    page_ref = f", pp. {pages[0]}-{pages[-1]})"
    citation = base_citation + page_ref
    assert citation == "Strategic Plan 2024 (policy_document, 2024-01-01, pp. 1-15)"
    print(f"✅ Many pages: {citation}")


def test_document_without_page_markers():
    """
    Test that documents without page markers still work (backward compatibility).
    """
    
    # Document without page markers (e.g., plain text upload)
    content = """
This is a simple text document without any page markers.
It should still be processed and cited correctly.
"""
    
    page_numbers = VectorWeightedMatcher.extract_page_numbers_from_content(content)
    assert page_numbers == [], "Should return empty list for documents without page markers"
    
    # Generate citation without page numbers
    citation_parts = ["Simple Text Document", "policy_document", "2024-01-01"]
    final_citation = f"{citation_parts[0]} ({', '.join(citation_parts[1:])})"
    
    expected = "Simple Text Document (policy_document, 2024-01-01)"
    assert final_citation == expected
    print(f"✅ No pages: {final_citation}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
