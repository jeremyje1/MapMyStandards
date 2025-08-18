#!/usr/bin/env python3
"""
A³E Administrator Testing Environment Setup

Creates a secure, password-protected testing environment for administrators
to validate system functionality before customer deployment.
"""

import os
import sys
import uuid
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

def generate_admin_credentials():
    """Generate secure admin credentials for testing environment"""
    admin_password = secrets.token_urlsafe(16)
    admin_api_key = f"a3e_admin_{secrets.token_urlsafe(24)}"
    admin_secret = secrets.token_urlsafe(32)
    
    return {
        "admin_password": admin_password,
        "admin_api_key": admin_api_key,
        "admin_secret": admin_secret,
        "admin_username": "a3e_admin"
    }

def create_staging_env_file(credentials: Dict[str, str]):
    """Create staging environment configuration"""
    
    staging_env = f"""# A³E Administrator Testing Environment
# Generated: {os.popen('date').read().strip()}
# Purpose: Secure testing environment for system validation

# Environment Configuration
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG

# API Configuration  
API_HOST=0.0.0.0
API_PORT=8001
API_PREFIX=/api/v1

# Admin Authentication
ADMIN_USERNAME={credentials['admin_username']}
ADMIN_PASSWORD_HASH={hashlib.sha256(credentials['admin_password'].encode()).hexdigest()}
ADMIN_API_KEY={credentials['admin_api_key']}
SECRET_KEY={credentials['admin_secret']}

# Testing Database (separate from production)
DATABASE_URL=sqlite:///./a3e_staging.db
REDIS_URL=redis://localhost:6379/1

# LLM Configuration (use same as production but with rate limits)
ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
OPENAI_API_KEY=${{OPENAI_API_KEY}}

# Testing Rate Limits (more restrictive)
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=3600

# Feature Flags for Testing
ENABLE_GRAPHQL=true
ENABLE_REAL_TIME_PROCESSING=true
ENABLE_BATCH_PROCESSING=true
ENABLE_AUTO_EVIDENCE_MAPPING=true

# CORS for staging
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://staging.mapmystandards.ai

# Testing Mode Flags
TESTING_MODE=true
ADMIN_TESTING_ENABLED=true
MOCK_PAYMENT_PROCESSING=true

# Monitoring (separate from production)
SENTRY_DSN=${{STAGING_SENTRY_DSN}}
PROMETHEUS_ENABLED=true
"""
    
    with open('.env.staging', 'w') as f:
        f.write(staging_env)
    
    print("✅ Created .env.staging configuration")

def create_admin_testing_script():
    """Create comprehensive testing script for administrators"""
    
    test_script = '''#!/usr/bin/env python3
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
        
        print(f"\\n📋 Test Report Summary:")
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
            print("\\n🎉 All tests passed! System ready for customer deployment.")
            return 0
        else:
            print("\\n⚠️  Some tests failed. Please review before customer deployment.")
            return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="A³E Administrator Testing Suite")
    parser.add_argument("--api-key", help="Admin API key for testing")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for testing")
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(run_admin_tests(args.api_key))
    sys.exit(exit_code)
'''
    
    with open('admin_test_suite.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('admin_test_suite.py', 0o755)
    print("✅ Created admin_test_suite.py")

def create_docker_staging():
    """Create Docker setup for isolated staging environment"""
    
    docker_compose = '''version: '3.8'

services:
  a3e-staging:
    build: .
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=staging
    env_file:
      - .env.staging
    volumes:
      - ./data/staging:/app/data
      - ./logs/staging:/app/logs
    depends_on:
      - redis-staging
      - postgres-staging
    networks:
      - a3e-staging-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.a3e-staging.rule=Host(`staging.mapmystandards.ai`)"
      - "traefik.http.routers.a3e-staging.tls=true"
      - "traefik.http.middlewares.staging-auth.basicauth.users=admin:$$2y$$10$$..."

  redis-staging:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis-staging-data:/data
    networks:
      - a3e-staging-net

  postgres-staging:
    image: postgres:15
    environment:
      POSTGRES_DB: a3e_staging
      POSTGRES_USER: a3e_staging
      POSTGRES_PASSWORD: staging_password_change_me
    ports:
      - "5433:5432"
    volumes:
      - postgres-staging-data:/var/lib/postgresql/data
    networks:
      - a3e-staging-net

  nginx-staging:
    image: nginx:alpine
    ports:
      - "8080:80"
      - "8443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - a3e-staging
    networks:
      - a3e-staging-net

volumes:
  redis-staging-data:
  postgres-staging-data:

networks:
  a3e-staging-net:
    driver: bridge
'''
    
    with open('docker-compose.staging.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✅ Created docker-compose.staging.yml")

def create_staging_startup_script():
    """Create startup script for staging environment"""
    
    startup_script = '''#!/bin/bash
set -e

echo "🚀 Starting A³E Administrator Testing Environment"
echo "=================================================="

# Check if credentials exist
if [ ! -f ".env.staging" ]; then
    echo "❌ Staging environment not configured. Run python admin_test_setup.py first"
    exit 1
fi

# Load staging environment
source .env.staging

echo "📋 Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  API Port: $API_PORT" 
echo "  Database: $DATABASE_URL"
echo "  Admin User: $ADMIN_USERNAME"

# Start staging environment
echo "🔧 Starting services..."

# Option 1: Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "🐳 Using Docker Compose..."
    docker-compose -f docker-compose.staging.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "🔍 Service Status:"
    docker-compose -f docker-compose.staging.yml ps
    
# Option 2: Direct Python
else
    echo "🐍 Starting with Python directly..."
    
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        echo "  Starting Redis..."
        redis-server --daemonize yes --port 6380
    fi
    
    # Start A³E in staging mode
    export ENVIRONMENT=staging
    python -m src.a3e.main --port 8001 &
    A3E_PID=$!
    
    echo "  A³E started with PID: $A3E_PID"
fi

echo "✅ Staging environment started!"
echo ""
echo "🔗 Access URLs:"
echo "  API: http://localhost:8001"
echo "  Health: http://localhost:8001/health"
echo "  Docs: http://localhost:8001/docs"
echo ""
echo "🔑 Admin Credentials:"
echo "  Username: $ADMIN_USERNAME"
echo "  API Key: $ADMIN_API_KEY"
echo ""
echo "🧪 To run tests:"
echo "  python admin_test_suite.py --api-key $ADMIN_API_KEY"
echo ""
echo "🛑 To stop staging:"
echo "  ./stop_staging.sh"
'''
    
    with open('start_staging.sh', 'w') as f:
        f.write(startup_script)
    
    os.chmod('start_staging.sh', 0o755)
    
    # Create stop script
    stop_script = '''#!/bin/bash
echo "🛑 Stopping A³E Staging Environment"

# Stop Docker Compose
if [ -f "docker-compose.staging.yml" ]; then
    docker-compose -f docker-compose.staging.yml down
fi

# Kill any Python processes
pkill -f "src.a3e.main"

# Stop Redis if we started it
if pgrep -f "redis-server.*6380" > /dev/null; then
    pkill -f "redis-server.*6380"
fi

echo "✅ Staging environment stopped"
'''
    
    with open('stop_staging.sh', 'w') as f:
        f.write(stop_script)
    
    os.chmod('stop_staging.sh', 0o755)
    
    print("✅ Created start_staging.sh and stop_staging.sh")

def main():
    """Main setup function"""
    print("🛡️  A³E Administrator Testing Environment Setup")
    print("=" * 60)
    
    # Generate admin credentials
    print("🔑 Generating admin credentials...")
    credentials = generate_admin_credentials()
    
    # Create configuration files
    create_staging_env_file(credentials)
    create_admin_testing_script()
    create_docker_staging()
    create_staging_startup_script()
    
    print("\n✅ Administrator testing environment setup complete!")
    print("\n📋 Next Steps:")
    print("1. Review .env.staging and update any necessary settings")
    print("2. Start staging environment: ./start_staging.sh")
    print("3. Run admin tests: python admin_test_suite.py --api-key <key>")
    print("4. Access staging API at: http://localhost:8001")
    
    print(f"\n🔑 Your Admin Credentials:")
    print(f"  Username: {credentials['admin_username']}")
    print(f"  Password: {credentials['admin_password']}")
    print(f"  API Key: {credentials['admin_api_key']}")
    
    print("\n⚠️  IMPORTANT: Save these credentials securely!")
    print("💾 Credentials also saved in .env.staging file")

if __name__ == "__main__":
    main()
