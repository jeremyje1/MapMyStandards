#!/usr/bin/env python3
"""
A3E API Integration Test

Tests basic functionality of all API endpoints to ensure the backend is working correctly.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class A3EAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    result = {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "success": response.status < 400,
                        "response": await response.json() if response.status < 500 else await response.text()
                    }
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, headers=headers) as response:
                    result = {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "success": response.status < 400,
                        "response": await response.json() if response.status < 500 else await response.text()
                    }
            else:
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status": 405,
                    "success": False,
                    "response": "Method not supported in test"
                }
                
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "success": False,
                "error": str(e)
            }
        
        return result
    
    async def run_basic_tests(self) -> Dict[str, Any]:
        """Run basic API tests"""
        logger.info("🧪 Starting A3E API Integration Tests...")
        
        test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        # Test endpoints
        test_cases = [
            # Root and health endpoints
            ("GET", "/"),
            ("GET", "/health"),
            
            # Institution endpoints
            ("GET", "/api/v1/institutions"),
            ("GET", "/api/v1/institution-types"),
            
            # Standards endpoints  
            ("GET", "/api/v1/standards"),
            ("GET", "/api/v1/accreditors"),
            ("GET", "/api/v1/categories"),
            
            # Evidence endpoints
            ("GET", "/api/v1/evidence"),
            ("GET", "/api/v1/evidence-types"),
            
            # Workflow endpoints
            ("GET", "/api/v1/workflows"),
            ("GET", "/api/v1/workflow-types"),
            ("GET", "/api/v1/workflow-statistics"),
        ]
        
        for method, endpoint in test_cases:
            logger.info(f"Testing {method} {endpoint}")
            result = await self.test_endpoint(method, endpoint)
            
            test_results["total_tests"] += 1
            if result["success"]:
                test_results["passed"] += 1
                logger.info(f"✅ {method} {endpoint} - Status: {result['status']}")
            else:
                test_results["failed"] += 1
                logger.error(f"❌ {method} {endpoint} - Status: {result['status']} - Error: {result.get('error', 'HTTP Error')}")
            
            test_results["results"].append(result)
        
        return test_results
    
    async def test_data_flow(self) -> Dict[str, Any]:
        """Test basic data creation flow"""
        logger.info("🔄 Testing data creation flow...")
        
        flow_results = {
            "institution_creation": None,
            "evidence_creation": None,
            "workflow_creation": None,
            "success": False
        }
        
        try:
            # Test institution creation
            institution_data = {
                "name": "Test University",
                "institution_types": ["university"],
                "state": "CA",
                "city": "Los Angeles",
                "control": "private",
                "total_enrollment": 5000,
                "website": "https://test-university.edu"
            }
            
            result = await self.test_endpoint("POST", "/api/v1/institutions", institution_data)
            flow_results["institution_creation"] = result
            
            if result["success"]:
                institution_id = result["response"].get("id")
                logger.info(f"✅ Created test institution with ID: {institution_id}")
                
                # Test evidence creation
                evidence_data = {
                    "title": "Test Evidence Document",
                    "description": "A test evidence document for API testing",
                    "institution_id": institution_id,
                    "evidence_type": "policy",
                    "tags": ["test", "api"]
                }
                
                result = await self.test_endpoint("POST", "/api/v1/evidence", evidence_data)
                flow_results["evidence_creation"] = result
                
                if result["success"]:
                    evidence_id = result["response"].get("id")
                    logger.info(f"✅ Created test evidence with ID: {evidence_id}")
                    
                    # Test workflow creation
                    workflow_data = {
                        "title": "Test Workflow",
                        "description": "A test workflow for API testing",
                        "institution_id": institution_id,
                        "accreditor_id": "wscuc",
                        "workflow_type": "evidence_mapping",
                        "target_standards": ["wscuc_1_1"]
                    }
                    
                    result = await self.test_endpoint("POST", "/api/v1/workflows", workflow_data)
                    flow_results["workflow_creation"] = result
                    
                    if result["success"]:
                        workflow_id = result["response"].get("id")
                        logger.info(f"✅ Created test workflow with ID: {workflow_id}")
                        flow_results["success"] = True
                    else:
                        logger.error(f"❌ Failed to create workflow: {result}")
                else:
                    logger.error(f"❌ Failed to create evidence: {result}")
            else:
                logger.error(f"❌ Failed to create institution: {result}")
                
        except Exception as e:
            logger.error(f"❌ Error in data flow test: {e}")
            flow_results["error"] = str(e)
        
        return flow_results

async def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    logger.info(f"🎯 Testing A3E API at: {base_url}")
    
    async with A3EAPITester(base_url) as tester:
        # Run basic endpoint tests
        basic_results = await tester.run_basic_tests()
        
        # Run data flow tests (only if basic tests mostly pass)
        flow_results = None
        if basic_results["passed"] > basic_results["failed"]:
            flow_results = await tester.test_data_flow()
        else:
            logger.warning("⚠️ Skipping data flow tests due to basic test failures")
        
        # Generate report
        logger.info("📊 Test Results Summary:")
        logger.info(f"   Basic Tests: {basic_results['passed']}/{basic_results['total_tests']} passed")
        
        if flow_results:
            flow_success = "✅" if flow_results["success"] else "❌"
            logger.info(f"   Data Flow: {flow_success}")
        
        # Save detailed results
        results = {
            "basic_tests": basic_results,
            "data_flow_tests": flow_results,
            "summary": {
                "overall_success": basic_results["passed"] > basic_results["failed"],
                "api_accessible": basic_results["total_tests"] > 0 and basic_results["results"][0]["success"],
                "data_operations": flow_results["success"] if flow_results else False
            }
        }
        
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("💾 Detailed results saved to test_results.json")
        
        # Exit with appropriate code
        if results["summary"]["overall_success"]:
            logger.info("🎉 API tests completed successfully!")
            return 0
        else:
            logger.error("💥 API tests failed!")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
