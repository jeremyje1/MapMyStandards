#!/usr/bin/env python3
"""
A³E Pre-Deployment Validation Script

This script validates that all components are ready for production deployment.
Run this before deploying to production to catch any configuration issues.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def print_status(message, status="info"):
    """Print formatted status message."""
    colors = {
        "info": "\033[94m",
        "success": "\033[92m", 
        "warning": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m"
    }
    
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️", 
        "error": "❌"
    }
    
    print(f"{colors[status]}{icons[status]} {message}{colors['reset']}")

def check_environment_file():
    """Check if production environment file exists and has required variables."""
    print_status("Checking production environment configuration...", "info")
    
    env_file = Path(".env.production")
    if not env_file.exists():
        print_status("Production environment file (.env.production) not found!", "error")
        print_status("Create it from .env.production.example", "warning")
        return False
    
    # Load and check required variables
    required_vars = [
        "POSTGRES_PASSWORD",
        "SECRET_KEY", 
        "REDIS_PASSWORD",
        "OPENAI_API_KEY",
        "CANVAS_ACCESS_TOKEN"
    ]
    
    missing_vars = []
    with open(env_file) as f:
        env_content = f.read()
        
    for var in required_vars:
        if f"{var}=" not in env_content or "CHANGE_ME" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print_status(f"Missing or placeholder values for: {', '.join(missing_vars)}", "error")
        return False
    
    print_status("Environment configuration looks good", "success")
    return True

def check_docker():
    """Check if Docker and Docker Compose are available."""
    print_status("Checking Docker installation...", "info")
    
    try:
        # Check Docker
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print_status("Docker is not available", "error")
            return False
        print_status(f"Docker: {result.stdout.strip()}", "success")
        
        # Check Docker Compose
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print_status("Docker Compose is not available", "error")
            return False
        print_status(f"Docker Compose: {result.stdout.strip()}", "success")
        
        return True
        
    except FileNotFoundError:
        print_status("Docker is not installed", "error")
        return False

def check_ports():
    """Check if required ports are available."""
    print_status("Checking port availability...", "info")
    
    required_ports = [80, 443, 5432, 6379, 19530]
    used_ports = []
    
    for port in required_ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                used_ports.append(port)
        except:
            pass
    
    if used_ports:
        print_status(f"Ports already in use: {used_ports}", "warning")
        print_status("You may need to stop other services or change port configuration", "warning")
    else:
        print_status("All required ports are available", "success")
    
    return True

def validate_local_deployment():
    """Test local deployment before production."""
    print_status("Validating local deployment...", "info")
    
    try:
        # Start local deployment
        print_status("Starting local test deployment...", "info")
        process = subprocess.Popen(
            ["docker-compose", "-f", "docker-compose.yml", "up", "-d"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(30)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print_status("Local deployment health check passed", "success")
                
                # Test API endpoints
                endpoints_to_test = [
                    "/docs",
                    "/api/v1/health", 
                    "/api/v1/standards/",
                    "/api/v1/proprietary/capabilities"
                ]
                
                working_endpoints = 0
                for endpoint in endpoints_to_test:
                    try:
                        resp = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                        if resp.status_code < 500:
                            working_endpoints += 1
                    except:
                        pass
                
                print_status(f"API endpoints working: {working_endpoints}/{len(endpoints_to_test)}", 
                           "success" if working_endpoints >= 3 else "warning")
                
            else:
                print_status(f"Health check failed: HTTP {response.status_code}", "error")
                return False
                
        except requests.exceptions.RequestException as e:
            print_status(f"Could not connect to local deployment: {e}", "error")
            return False
        
        finally:
            # Clean up
            print_status("Stopping test deployment...", "info")
            subprocess.run(["docker-compose", "-f", "docker-compose.yml", "down"], 
                         capture_output=True)
        
        return True
        
    except Exception as e:
        print_status(f"Local deployment test failed: {e}", "error")
        return False

def check_disk_space():
    """Check if there's enough disk space."""
    print_status("Checking disk space...", "info")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        
        # Convert to GB
        free_gb = free // (1024**3)
        
        if free_gb < 10:
            print_status(f"Low disk space: {free_gb}GB free (need at least 10GB)", "error")
            return False
        elif free_gb < 20:
            print_status(f"Disk space warning: {free_gb}GB free (recommend 20GB+)", "warning")
        else:
            print_status(f"Disk space OK: {free_gb}GB free", "success")
        
        return True
        
    except Exception as e:
        print_status(f"Could not check disk space: {e}", "warning")
        return True

def main():
    """Run all pre-deployment checks."""
    print("🚀 A³E Pre-Deployment Validation")
    print("================================")
    print()
    
    checks = [
        ("Environment Configuration", check_environment_file),
        ("Docker Installation", check_docker),
        ("Port Availability", check_ports),
        ("Disk Space", check_disk_space),
        ("Local Deployment Test", validate_local_deployment)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}")
        print("-" * (len(name) + 4))
        
        try:
            if check_func():
                passed += 1
            else:
                print_status(f"{name} check failed", "error")
        except Exception as e:
            print_status(f"{name} check error: {e}", "error")
    
    print("\n" + "="*50)
    print("📊 Pre-Deployment Summary")
    print("="*50)
    
    if passed == total:
        print_status(f"All checks passed ({passed}/{total})! 🎉", "success")
        print_status("Your A³E system is ready for production deployment!", "success")
        print()
        print("Next steps:")
        print("1. Run './deploy.sh' to deploy to production")
        print("2. Configure your domain DNS")
        print("3. Set up SSL certificates")
        print("4. Start your pilot testing!")
        return 0
    else:
        print_status(f"Some checks failed ({passed}/{total})", "error")
        print_status("Please fix the issues above before deploying to production", "warning")
        return 1

if __name__ == "__main__":
    sys.exit(main())
