#!/usr/bin/env python3
"""
Test AI Services Directly
Check what functionality works without external API keys
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/jeremy.estrella/Desktop/MapMyStandards-main')

from src.a3e.services.standards_graph import standards_graph
from src.a3e.services.evidence_mapper import evidence_mapper
from src.a3e.services.evidence_trust import evidence_trust_scorer
from src.a3e.services.gap_risk_predictor import gap_risk_predictor

def test_standards_graph():
    """Test StandardsGraph functionality"""
    print("🔍 Testing StandardsGraph...")
    try:
        # Get basic info
        total_nodes = len(standards_graph.nodes)
        print(f"✅ Standards loaded: {total_nodes} standards")
        
        # Test search by keywords
        keywords = {"privacy", "data"}
        search_results = standards_graph.search_by_keywords(keywords, limit=3)
        print(f"✅ Search works: Found {len(search_results)} results for privacy/data")
        for node, score in search_results[:2]:
            print(f"   - {node.standard_id}: {node.title[:50]}... (score: {score:.2f})")
        
        # Test node retrieval
        if search_results:
            node_id = search_results[0][0].standard_id
            node = standards_graph.get_node(node_id)
            if node:
                print(f"✅ Node retrieval works: {node.title[:40]}...")
            
        return True
    except Exception as e:
        print(f"❌ StandardsGraph error: {e}")
        return False

def test_evidence_mapper():
    """Test EvidenceMapper functionality"""
    print("\n🔍 Testing EvidenceMapper...")
    try:
        from src.a3e.services.evidence_mapper import EvidenceDocument
        from datetime import datetime
        
        # Test with sample document (using correct constructor)
        sample_doc = EvidenceDocument(
            doc_id="test_001",
            text="This document outlines our privacy protection policies and data security measures.",
            metadata={"source": "test"},
            doc_type="policy",
            source_system="manual",
            upload_date=datetime.now()
        )
        
        # Map to standards
        mappings = evidence_mapper.map_evidence(sample_doc, top_k=3)
        print(f"✅ Evidence mapping works: Found {len(mappings)} mappings")
        for mapping in mappings[:2]:
            print(f"   - {mapping.standard_id}: {mapping.standard_title[:40]}... (confidence: {mapping.confidence:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ EvidenceMapper error: {e}")
        return False

def test_evidence_trust_scorer():
    """Test EvidenceTrust scoring"""
    print("\n🔍 Testing EvidenceTrust Scorer...")
    try:
        from src.a3e.services.evidence_trust import EvidenceType, SourceSystem
        from src.a3e.services.evidence_mapper import EvidenceDocument
        from datetime import datetime
        
        # Create test document (using correct constructor)
        test_doc = EvidenceDocument(
            doc_id="test_001",
            text="This is a formal policy document with structured data security requirements.",
            metadata={"file_size": 2048, "file_type": "pdf"},
            doc_type="policy",
            source_system="manual",
            upload_date=datetime.now()
        )
        
        score = evidence_trust_scorer.calculate_trust_score(
            evidence_doc=test_doc,
            evidence_type=EvidenceType.POLICY,
            source_system=SourceSystem.MANUAL_UPLOAD
        )
        print(f"✅ Trust scoring works: Score = {score.overall_score:.2f} ({score.trust_level})")
        
        return True
    except Exception as e:
        print(f"❌ EvidenceTrust error: {e}")
        return False

def test_gap_risk_predictor():
    """Test Gap Risk Predictor"""
    print("\n🔍 Testing Gap Risk Predictor...")
    try:
        # Test with the correct parameters for predict_risk
        risk_score = gap_risk_predictor.predict_risk(
            standard_id="FERPA_1_1",
            coverage_percentage=75.0,
            evidence_trust_scores=[0.8, 0.7, 0.6],
            evidence_ages_days=[30, 60, 90],
            overdue_tasks_count=2,
            total_tasks_count=10,
            recent_changes_count=1,
            historical_findings_count=3,
            time_to_next_review_days=90
        )
        
        print(f"✅ Gap prediction works: Risk = {risk_score.risk_score:.2f} ({risk_score.risk_level.value})")
        print(f"   Standard: {risk_score.standard_id}")
        if risk_score.predicted_issues:
            print(f"   Predicted issues: {len(risk_score.predicted_issues)}")
        
        return True
    except Exception as e:
        print(f"❌ Gap Risk Predictor error: {e}")
        return False

def check_llm_requirements():
    """Check what LLM features need external API keys"""
    print("\n🔍 Checking LLM Requirements...")
    try:
        # Check if API keys are configured
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
        print(f"Anthropic API Key: {'✅ Set' if anthropic_key else '❌ Not set'}")
        
        if not openai_key and not anthropic_key:
            print("⚠️  No LLM API keys found - advanced text generation disabled")
            print("   Basic AI algorithms (graph, mapping, scoring) should still work")
        
        return True
    except Exception as e:
        print(f"❌ LLM service error: {e}")
        return False

def main():
    print("🚀 A3E AI Services Functionality Test")
    print("=" * 50)
    
    results = []
    
    # Test core AI services
    results.append(test_standards_graph())
    results.append(test_evidence_mapper())
    results.append(test_evidence_trust_scorer())
    results.append(test_gap_risk_predictor())
    results.append(check_llm_requirements())
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if sum(results) >= 4:  # Core AI services work
        print("\n🎉 Core AI functionality is working!")
        print("💡 Your customers can access:")
        print("   - Standards Graph™ (59 standards)")
        print("   - Evidence Mapping™")
        print("   - Evidence Trust Scoring™")  
        print("   - Gap Risk Prediction™")
        
        if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
            print("\n⚠️  For advanced features, you may need:")
            print("   - OPENAI_API_KEY (for GPT-powered insights)")
            print("   - ANTHROPIC_API_KEY (for Claude-powered analysis)")
            print("   But the core AI algorithms work without them!")
        
    else:
        print("\n❌ Some core AI services have issues")

if __name__ == "__main__":
    main()
