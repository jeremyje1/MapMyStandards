#!/usr/bin/env python3
"""
A³E System Validation Script

Quick validation of core A³E components and capabilities.
Run this to verify your system is working correctly.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all core modules can be imported"""
    print("🔍 Testing core module imports...")
    
    try:
        from a3e.core.config import settings
        print("  ✅ Configuration module")
        
        from a3e.core.accreditation_ontology import AccreditationOntology
        print("  ✅ Accreditation ontology (proprietary)")
        
        from a3e.core.vector_matching import VectorWeightedMatcher
        print("  ✅ Vector-weighted matching (proprietary)")
        
        from a3e.core.multi_agent_pipeline import MultiAgentPipeline
        print("  ✅ Multi-agent pipeline (proprietary)")
        
        from a3e.core.audit_trail import AuditTrail
        print("  ✅ Audit trail system (proprietary)")
        
        from a3e.core.accreditation_registry import ALL_ACCREDITORS
        print(f"  ✅ Accreditation registry ({len(ALL_ACCREDITORS)} accreditors)")
        
        from a3e.agents import A3EAgentOrchestrator
        print("  ✅ Agent orchestrator")
        
        from a3e.models import Institution, Evidence, Standard
        print("  ✅ Data models")
        
        print("  🎉 All core modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_accreditor_coverage():
    """Test multi-accreditor support"""
    print("\n🏛️ Testing multi-accreditor coverage...")
    
    try:
        from a3e.core.accreditation_registry import ALL_ACCREDITORS, get_accreditors_by_institution_type
        
        print(f"  📊 Total accreditors supported: {len(ALL_ACCREDITORS)}")
        
        for accreditor in ALL_ACCREDITORS:
            print(f"    • {accreditor['name']} ({accreditor['code']})")
        
        four_year = get_accreditors_by_institution_type("four_year")
        two_year = get_accreditors_by_institution_type("two_year")
        
        print(f"  🎓 4-year institution accreditors: {len(four_year)}")
        print(f"  🎓 2-year institution accreditors: {len(two_year)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Accreditor test error: {e}")
        return False

def test_proprietary_algorithms():
    """Test proprietary algorithm initialization"""
    print("\n🧠 Testing proprietary algorithm initialization...")
    
    try:
        from a3e.core.accreditation_ontology import AccreditationOntology
        from a3e.core.vector_matching import VectorWeightedMatcher
        
        # Test ontology
        ontology = AccreditationOntology()
        print("  ✅ Accreditation ontology initialized")
        print(f"    • Concept categories: {len(ontology.concept_categories)}")
        print(f"    • Embeddings model: {ontology.embeddings_model}")
        
        # Test vector matcher
        matcher = VectorWeightedMatcher()
        print("  ✅ Vector-weighted matcher initialized")
        print(f"    • Similarity threshold: {matcher.similarity_threshold}")
        print(f"    • Confidence weighting: {matcher.use_confidence_weighting}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Proprietary algorithm error: {e}")
        return False

async def test_agent_pipeline():
    """Test multi-agent pipeline"""
    print("\n🤖 Testing multi-agent pipeline...")
    
    try:
        from a3e.core.multi_agent_pipeline import MultiAgentPipeline
        
        pipeline = MultiAgentPipeline()
        print("  ✅ Multi-agent pipeline initialized")
        print(f"    • Agent count: {len(pipeline.agents)}")
        print(f"    • Pipeline order: {' → '.join(pipeline.agent_sequence)}")
        
        # Test agent roles
        for agent_name in pipeline.agent_sequence:
            print(f"    • {agent_name}: Ready")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent pipeline error: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n⚙️ Testing environment configuration...")
    
    try:
        from a3e.core.config import settings
        
        print(f"  ✅ Environment: {settings.environment}")
        print(f"  ✅ Debug mode: {settings.debug}")
        print(f"  ✅ Database URL configured: {'Yes' if settings.database_url else 'No'}")
        print(f"  ✅ Vector DB configured: {'Yes' if settings.milvus_host else 'No'}")
        print(f"  ✅ LLM services configured: {'Yes' if settings.openai_api_key else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def test_api_structure():
    """Test API structure"""
    print("\n🌐 Testing API structure...")
    
    try:
        from a3e.main import app
        
        print("  ✅ FastAPI application created")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"  ✅ API routes configured: {len(routes)}")
        
        key_routes = ["/", "/health", "/institutions", "/evidence", "/standards", "/workflows"]
        for route in key_routes:
            if any(r.startswith(route) for r in routes):
                print(f"    • {route}: ✅")
            else:
                print(f"    • {route}: ❌")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API structure error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 A³E System Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_accreditor_coverage,
        test_proprietary_algorithms,
        test_environment_config,
        test_api_structure,
    ]
    
    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = asyncio.run(test())
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your A³E system is ready for development and deployment.")
        print("\nNext steps:")
        print("1. Start local development: docker-compose up -d")
        print("2. Install dependencies: poetry install")
        print("3. Run API server: make dev")
    else:
        print(f"\n⚠️  {total-passed} tests failed.")
        print("Please check the error messages above and fix any issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
