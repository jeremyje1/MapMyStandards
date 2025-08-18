#!/usr/bin/env python3
"""
A3E System Setup and Validation Script

Initializes the A3E system, seeds data, and validates all components are working.
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class A3ESystemSetup:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.server_process = None
        
    def run_command(self, command: str, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command"""
        cwd = cwd or self.project_root
        logger.info(f"Running: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd, 
                capture_output=True, 
                text=True,
                check=check
            )
            
            if result.stdout:
                logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr and result.returncode != 0:
                logger.error(f"STDERR: {result.stderr}")
                
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"STDERR: {e.stderr}")
            if check:
                raise
            return e
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        logger.info("🔍 Checking prerequisites...")
        
        checks = [
            ("python3", "python3 --version"),
            ("poetry", "poetry --version"),
            ("docker", "docker --version"),
            ("docker-compose", "docker-compose --version"),
        ]
        
        all_good = True
        for name, command in checks:
            try:
                result = self.run_command(command, check=False)
                if result.returncode == 0:
                    logger.info(f"✅ {name}: {result.stdout.strip()}")
                else:
                    logger.error(f"❌ {name}: Not found or not working")
                    all_good = False
            except Exception as e:
                logger.error(f"❌ {name}: Error checking - {e}")
                all_good = False
        
        return all_good
    
    def setup_environment(self) -> bool:
        """Setup the development environment"""
        logger.info("🛠️ Setting up environment...")
        
        try:
            # Install Python dependencies
            logger.info("Installing Python dependencies...")
            self.run_command("poetry install")
            
            # Start Docker services
            logger.info("Starting Docker services...")
            self.run_command("docker-compose up -d postgres milvus redis")
            
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            time.sleep(10)
            
            # Initialize database
            logger.info("Initializing database...")
            self.run_command("make init-db")
            
            # Run migrations
            logger.info("Running database migrations...")
            self.run_command("poetry run alembic upgrade head")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            return False
    
    def seed_data(self) -> bool:
        """Seed the database with initial data"""
        logger.info("🌱 Seeding database...")
        
        try:
            self.run_command("poetry run python scripts/seed_data.py")
            logger.info("✅ Database seeded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database seeding failed: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the A3E server"""
        logger.info("🚀 Starting A3E server...")
        
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                ["poetry", "run", "uvicorn", "src.a3e.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            logger.info("Waiting for server to start...")
            time.sleep(5)
            
            # Check if server is still running
            if self.server_process.poll() is None:
                logger.info("✅ Server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"❌ Server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the A3E server"""
        if self.server_process:
            logger.info("🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.server_process.kill()
                self.server_process.wait()
            
            self.server_process = None
            logger.info("✅ Server stopped")
    
    def test_api(self) -> bool:
        """Test the API endpoints"""
        logger.info("🧪 Testing API...")
        
        try:
            result = self.run_command("poetry run python scripts/test_api.py")
            logger.info("✅ API tests completed")
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"❌ API tests failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")
        
        # Stop server
        self.stop_server()
        
        # Stop Docker services
        try:
            self.run_command("docker-compose down", check=False)
            logger.info("✅ Docker services stopped")
        except Exception as e:
            logger.warning(f"Warning: Failed to stop Docker services: {e}")
    
    def run_full_setup(self) -> bool:
        """Run the complete setup process"""
        logger.info("🎯 Starting A3E System Setup...")
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("❌ Prerequisites check failed")
                return False
            
            # Setup environment
            if not self.setup_environment():
                logger.error("❌ Environment setup failed")
                return False
            
            # Seed data
            if not self.seed_data():
                logger.error("❌ Data seeding failed")
                return False
            
            # Start server
            if not self.start_server():
                logger.error("❌ Server startup failed")
                return False
            
            # Test API
            api_success = self.test_api()
            
            if api_success:
                logger.info("🎉 A3E System Setup completed successfully!")
                logger.info("🌐 Server is running at: http://localhost:8000")
                logger.info("📚 API documentation: http://localhost:8000/docs")
                logger.info("🔄 To stop the server, press Ctrl+C")
                
                # Keep server running until interrupted
                try:
                    while self.server_process and self.server_process.poll() is None:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("🛑 Received interrupt signal")
                
                return True
            else:
                logger.error("❌ API tests failed")
                return False
                
        except KeyboardInterrupt:
            logger.info("🛑 Setup interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Setup failed with error: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Create setup instance
    setup = A3ESystemSetup(project_root)
    
    # Handle signals
    def signal_handler(signum, frame):
        logger.info("🛑 Received signal, cleaning up...")
        setup.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run setup
    success = setup.run_full_setup()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
