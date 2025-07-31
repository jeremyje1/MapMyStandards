#!/usr/bin/env python3
"""
A³E API Endpoint Testing Script

Comprehensive testing of all API endpoints with real requests.
"""

import requests
import json
import time
from typing import Dict, Any

class A3EAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                     expected_status: int = 200, description: str = "") -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "description": description,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time": round(response_time * 1000, 2),  # ms
                "success": response.status_code == expected_status,
                "response_size": len(response.content),
                "content_type": response.headers.get('content-type', 'Unknown')
            }
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = "Invalid JSON"
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "description": description,
                "status_code": 0,
                "expected_status": expected_status,
                "response_time": 0,
                "success": False,
                "error": str(e)
            }
            self.results.append(result)
            return result
    
    def run_comprehensive_tests(self):
        """Run comprehensive API testing"""
        print("🚀 A³E API Comprehensive Testing")
        print("=" * 50)
        
        # Health and Basic Endpoints
        print("\n📋 Basic System Endpoints")
        print("-" * 30)
        
        tests = [
            ("GET", "/", 200, "Landing page"),
            ("GET", "/health", 200, "Health check"),
            ("GET", "/docs", 200, "API documentation"),
            ("GET", "/redoc", 200, "ReDoc documentation"),
            ("GET", "/openapi.json", 200, "OpenAPI schema"),
        ]
        
        for method, endpoint, expected, desc in tests:
            result = self.test_endpoint(method, endpoint, expected_status=expected, description=desc)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {endpoint} ({result['response_time']}ms)")
        
        # Standards and Accreditation
        print("\n🏛️ Standards & Accreditation Endpoints")
        print("-" * 40)
        
        standards_tests = [
            ("GET", "/api/v1/standards/", 200, "List all standards"),
            ("GET", "/api/v1/standards/accreditors", 200, "List accreditors"),
            ("GET", "/api/v1/standards/search?query=mission", 200, "Search standards"),
        ]
        
        for method, endpoint, expected, desc in standards_tests:
            result = self.test_endpoint(method, endpoint, expected_status=expected, description=desc)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {endpoint} ({result['response_time']}ms)")
        
        # Proprietary Features
        print("\n🧠 Proprietary A³E Features")
        print("-" * 30)
        
        proprietary_tests = [
            ("GET", "/api/v1/proprietary/capabilities", 200, "Proprietary capabilities overview"),
            ("GET", "/api/v1/proprietary/ontology/concepts", 200, "Accreditation ontology concepts"),
            ("GET", "/api/v1/proprietary/vector/health", 200, "Vector matching service health"),
        ]
        
        for method, endpoint, expected, desc in proprietary_tests:
            result = self.test_endpoint(method, endpoint, expected_status=expected, description=desc)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {endpoint} ({result['response_time']}ms)")
        
        # Integration Endpoints
        print("\n🔗 Integration Endpoints")
        print("-" * 25)
        
        integration_tests = [
            ("GET", "/api/v1/integrations/", 200, "Integration status"),
            ("GET", "/api/v1/integrations/canvas/courses", 200, "Canvas courses"),
        ]
        
        for method, endpoint, expected, desc in integration_tests:
            result = self.test_endpoint(method, endpoint, expected_status=expected, description=desc)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {endpoint} ({result['response_time']}ms)")
        
        # Advanced Features (POST endpoints)
        print("\n⚡ Advanced Analysis Features")
        print("-" * 30)
        
        # Test evidence analysis
        sample_evidence = {
            "evidence_title": "Sample Evidence Document", 
            "evidence_content": "This is a sample evidence document for testing the A³E analysis pipeline.",
            "evidence_type": "policy_document",
            "standards_to_check": ["mission_governance", "academic_programs"]
        }
        
        result = self.test_endpoint(
            "POST", 
            "/api/v1/proprietary/analyze/evidence", 
            data=sample_evidence,
            expected_status=200,
            description="Evidence analysis with multi-agent pipeline"
        )
        status = "✅" if result["success"] else "❌"
        print(f"  {status} Evidence Analysis ({result.get('response_time', 0)}ms)")
        
        # Performance Summary
        self.print_performance_summary()
    
    def print_performance_summary(self):
        """Print performance and success summary"""
        print("\n" + "=" * 50)
        print("📊 TESTING SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        avg_response_time = sum(r.get("response_time", 0) for r in self.results) / total_tests if total_tests > 0 else 0
        
        print(f"Total endpoints tested: {total_tests}")
        print(f"Successful responses: {successful_tests}")
        print(f"Failed responses: {failed_tests}")
        print(f"Success rate: {(successful_tests/total_tests*100):.1f}%")
        print(f"Average response time: {avg_response_time:.1f}ms")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Endpoints:")
            for result in self.results:
                if not result["success"]:
                    error_msg = result.get('error', f'Status {result["status_code"]}')
                    print(f"  • {result['method']} {result['endpoint']} - {error_msg}") 
        
        print(f"\n🚀 A³E API is {'fully operational' if failed_tests == 0 else 'partially operational'}!")

if __name__ == "__main__":
    tester = A3EAPITester()
    tester.run_comprehensive_tests()
