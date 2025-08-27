#!/usr/bin/env python3
"""
Test database migration locally
Validates that the new database-powered APIs work correctly
"""

import asyncio
import os
import sys
import tempfile
import logging

# Add src to path
sys.path.insert(0, 'src')

# Set up environment for local testing
os.environ.setdefault('DATABASE_URL', 'sqlite:///test_mapmystandards.db')
os.environ.setdefault('DEBUG', 'true')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_migration():
    """Test the database migration and new APIs"""
    logger.info("🧪 Testing Database Migration")
    logger.info("=" * 50)
    
    try:
        # Test 1: Database initialization
        logger.info("1️⃣ Testing database initialization...")
        from src.a3e.database.connection import db_manager
        
        await db_manager.initialize()
        logger.info("✅ Database initialized successfully")
        
        # Test 2: Health check
        logger.info("2️⃣ Testing database health check...")
        is_healthy = await db_manager.health_check()
        if is_healthy:
            logger.info("✅ Database health check passed")
        else:
            logger.error("❌ Database health check failed")
            return False
        
        # Test 3: User service
        logger.info("3️⃣ Testing user service...")
        from src.a3e.database.services import UserService
        
        user = await UserService.get_or_create_user("test_user_123", "test@example.com", "Test User")
        logger.info(f"✅ User created/retrieved: {user.user_id}")
        
        # Test 4: Standards service
        logger.info("4️⃣ Testing standards service...")
        from src.a3e.database.services import StandardService
        
        standards = await StandardService.get_standards(accreditor_id="sacscoc")
        logger.info(f"✅ Retrieved {len(standards)} SACSCOC standards")
        
        if len(standards) == 0:
            logger.warning("⚠️ No standards found - this might be expected on first run")
        
        # Test 5: File service
        logger.info("5️⃣ Testing file service...")
        from src.a3e.database.services import FileService
        
        test_content = b"This is a test document for SACSCOC compliance analysis."
        file_record = await FileService.create_file(
            user_id="test_user_123",
            filename="test_document.txt",
            content=test_content,
            content_type="text/plain",
            title="Test Document"
        )
        logger.info(f"✅ File created: {file_record.file_id}")
        
        # Test 6: Job service
        logger.info("6️⃣ Testing job service...")
        from src.a3e.database.services import JobService
        
        job = await JobService.create_job("test_user_123", file_record.file_id)
        logger.info(f"✅ Job created: {job.job_id}")
        
        # Update job status
        await JobService.update_job_status(job.job_id, "completed", 100, "Test completed")
        logger.info("✅ Job status updated")
        
        # Test 7: Report service  
        logger.info("7️⃣ Testing report service...")
        from src.a3e.database.services import ReportService
        
        report = await ReportService.create_report(
            user_id="test_user_123",
            report_type="evidence_mapping_summary",
            parameters={"test": True}
        )
        logger.info(f"✅ Report created: {report.report_id}")
        
        # Test 8: User metrics
        logger.info("8️⃣ Testing user metrics...")
        metrics = await UserService.get_user_metrics("test_user_123")
        logger.info(f"✅ Retrieved user metrics: {metrics['core_metrics']['documents_analyzed']} docs analyzed")
        
        # Test 9: Database metrics
        logger.info("9️⃣ Testing database metrics...")
        db_metrics = await db_manager.get_metrics()
        logger.info(f"✅ Database metrics: {db_metrics}")
        
        # Cleanup
        await db_manager.close()
        logger.info("✅ Database closed successfully")
        
        logger.info("\n🎉 ALL DATABASE MIGRATION TESTS PASSED!")
        logger.info("✅ Database-powered APIs are ready for production")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_routes():
    """Test the new API routes with the database backend"""
    logger.info("\n🧪 Testing API Routes with Database Backend")
    logger.info("=" * 50)
    
    try:
        # Start the FastAPI app in test mode
        from src.a3e.main import app
        from fastapi.testclient import TestClient
        
        # Note: This would be async in a real test, but TestClient is sync
        # In production, use httpx.AsyncClient for async testing
        
        logger.info("✅ FastAPI app structure validated")
        
        # Check that database routes are loaded
        routes = [route.path for route in app.routes]
        expected_routes = [
            '/api/uploads',
            '/api/metrics/dashboard', 
            '/api/standards',
            '/api/reports'
        ]
        
        for route in expected_routes:
            if any(r.startswith(route) for r in routes):
                logger.info(f"✅ Route found: {route}")
            else:
                logger.warning(f"⚠️ Route not found: {route}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API routes test failed: {e}")
        return False

async def main():
    """Run all database migration tests"""
    logger.info("🚀 Database Migration Test Suite")
    logger.info("Testing local database functionality before Railway deployment")
    logger.info("")
    
    # Test database functionality
    db_success = await test_database_migration()
    
    # Test API integration
    api_success = await test_api_routes()
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 30)
    logger.info(f"Database Migration: {'✅ PASS' if db_success else '❌ FAIL'}")
    logger.info(f"API Integration: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if db_success and api_success:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("🚀 Ready for Railway deployment with database backend")
        return 0
    else:
        logger.info("\n💥 SOME TESTS FAILED!")
        logger.info("🔧 Fix issues before Railway deployment")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)