#!/usr/bin/env python3
"""
A³E Administrator Testing Suite

Comprehensive testing script to validate all system components
before customer deployment.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

class A3EAdminTester:
    def __init__(self, base_url: str = "http://localhost:8001", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"X-API-Key": self.api_key} if self.api_key else {}
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def test_system_health(self):
        """Test basic system health and availability"""
        print("🔍 Testing System Health...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data.get("status") == "healthy"
                self.log_success("System Health", "All services operational")
        except Exception as e:
            self.log_failure("System Health", str(e))
    
    async def test_authentication(self):
        """Test authentication and API key validation"""
        print("🔐 Testing Authentication...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/status") as resp:
                assert resp.status == 200
                self.log_success("Authentication", "API key validation working")
        except Exception as e:
            self.log_failure("Authentication", str(e))
    
    async def test_document_upload(self):
        """Test document upload and processing"""
        print("📄 Testing Document Upload...")
        
        # Create test document
        test_content = b"This is a test document for A3E validation."
        
        try:
            data = aiohttp.FormData()
            data.add_field('file', test_content, filename='test_doc.txt', content_type='text/plain')
            
            async with self.session.post(f"{self.base_url}/api/v1/upload", data=data) as resp:
                result = await resp.json()
                assert resp.status == 200
                assert "document_id" in result
                self.log_success("Document Upload", f"Uploaded: {result.get('document_id')}")
        except Exception as e:
            self.log_failure("Document Upload", str(e))
    
    async def test_evidence_mapping(self):
        """Test AI evidence mapping functionality"""
        print("🤖 Testing Evidence Mapping...")
        
        try:
            test_payload = {
                "text": "Our university maintains comprehensive student records and academic transcripts.",
                "institution_type": "university",
                "accreditor": "SACSCOC"
            }
            
            async with self.session.post(f"{self.base_url}/api/v1/evidence/map", json=test_payload) as resp:
                result = await resp.json()
                assert resp.status == 200
                assert "mappings" in result
                self.log_success("Evidence Mapping", f"Mapped to {len(result.get('mappings', []))} standards")
        except Exception as e:
            self.log_failure("Evidence Mapping", str(e))
    
    async def test_gap_analysis(self):
        """Test gap analysis functionality"""
        print("📊 Testing Gap Analysis...")
        
        try:
            test_payload = {
                "institution_id": "test_institution",
                "accreditor": "SACSCOC"
            }
            
            async with self.session.post(f"{self.base_url}/api/v1/analysis/gaps", json=test_payload) as resp:
                result = await resp.json()
                assert resp.status == 200
                assert "gaps" in result
                self.log_success("Gap Analysis", f"Found {len(result.get('gaps', []))} gaps")
        except Exception as e:
            self.log_failure("Gap Analysis", str(e))
    
    async def test_narrative_generation(self):
        """Test narrative generation"""
        print("📝 Testing Narrative Generation...")
        
        try:
            test_payload = {
                "standard_id": "SACSCOC.2.1",
                "evidence_ids": ["test_evidence_1"],
                "institution_context": "Test University"
            }
            
            async with self.session.post(f"{self.base_url}/api/v1/narrative/generate", json=test_payload) as resp:
                result = await resp.json()
                assert resp.status == 200
                assert "narrative" in result
                self.log_success("Narrative Generation", "Generated successfully")
        except Exception as e:
            self.log_failure("Narrative Generation", str(e))
    
    async def test_integration_endpoints(self):
        """Test Canvas and other integration endpoints"""
        print("🔌 Testing Integration Endpoints...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/integrations/canvas/health") as resp:
                result = await resp.json()
                assert resp.status == 200
                self.log_success("Canvas Integration", "Health check passed")
        except Exception as e:
            self.log_failure("Canvas Integration", str(e))
    
    def log_success(self, test_name: str, message: str):
        result = {"test": test_name, "status": "PASS", "message": message, "timestamp": datetime.now().isoformat()}
        self.test_results.append(result)
        print(f"  ✅ {test_name}: {message}")
    
    def log_failure(self, test_name: str, error: str):
        result = {"test": test_name, "status": "FAIL", "error": error, "timestamp": datetime.now().isoformat()}
        self.test_results.append(result)
        print(f"  ❌ {test_name}: {error}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        total = len(self.test_results)
        
        print(f"\n📋 Test Report Summary:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "  Success Rate: 0%")
        
        # Save detailed report
        with open(f"a3e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        return failed == 0

async def run_admin_tests(api_key: str = None):
    """Run comprehensive administrator tests"""
    print("🚀 Starting A³E Administrator Testing Suite")
    print("=" * 60)
    
    async with A3EAdminTester(api_key=api_key) as tester:
        # Core functionality tests
        await tester.test_system_health()
        await tester.test_authentication()
        await tester.test_document_upload()
        await tester.test_evidence_mapping()
        await tester.test_gap_analysis()
        await tester.test_narrative_generation()
        await tester.test_integration_endpoints()
        
        # Generate final report
        success = tester.generate_report()
        
        if success:
            print("\n🎉 All tests passed! System ready for customer deployment.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Please review before customer deployment.")
            return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="A³E Administrator Testing Suite")
    parser.add_argument("--api-key", help="Admin API key for testing")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for testing")
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(run_admin_tests(args.api_key))
    sys.exit(exit_code)
