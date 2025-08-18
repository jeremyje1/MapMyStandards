#!/usr/bin/env python3
"""
A³E System Health Check & Setup Validation
Checks all dependencies, configuration, and services.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from dotenv import load_dotenv

def check_mark(passed):
    return "✅" if passed else "❌"

def run_health_check():
    print("🔍 A³E System Health Check\n")
    
    issues = []
    all_good = True
    
    # Load environment
    load_dotenv()
    
    print("📦 Python Dependencies:")
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "alembic", "psycopg2", 
        "redis", "celery", "strawberry-graphql", "boto3", "openai",
        "anthropic", "sentence-transformers", "pypdf", "python-docx",
        "pandas", "numpy", "requests", "pydantic", "jinja2", "stripe"
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"  {check_mark(True)} {package}")
        except ImportError:
            print(f"  {check_mark(False)} {package} - Missing!")
            issues.append(f"Install missing package: pip install {package}")
            all_good = False
    
    print("\n🔧 Environment Configuration:")
    
    # Critical environment variables
    critical_vars = [
        ("DATABASE_URL", "postgresql://"),
        ("REDIS_URL", "redis://"),
        ("AWS_ACCESS_KEY_ID", "AKIA"),
        ("SECRET_KEY", None),
        ("CANVAS_ACCESS_TOKEN", None),
    ]
    
    for var, prefix in critical_vars:
        value = os.getenv(var)
        if value and (not prefix or value.startswith(prefix)):
            print(f"  {check_mark(True)} {var}")
        else:
            print(f"  {check_mark(False)} {var} - {'Missing' if not value else 'Invalid format'}")
            issues.append(f"Configure {var} in .env file")
            all_good = False
    
    # Optional but important variables
    print("\n🎯 Business Configuration:")
    business_vars = [
        ("STRIPE_SECRET_KEY", "sk_"),
        ("STRIPE_PUBLISHABLE_KEY", "pk_"),
        ("OPENAI_API_KEY", "sk-"),
        ("ANTHROPIC_API_KEY", "sk-"),
    ]
    
    for var, prefix in business_vars:
        value = os.getenv(var)
        if value and value.startswith(prefix) and "your_" not in value:
            print(f"  {check_mark(True)} {var}")
        else:
            print(f"  {check_mark(False)} {var} - Not configured")
            if var.startswith("STRIPE"):
                issues.append("Get Stripe API keys from https://dashboard.stripe.com/apikeys")
            elif "OPENAI" in var:
                issues.append("Get OpenAI API key from https://platform.openai.com/api-keys")
            elif "ANTHROPIC" in var:
                issues.append("Get Anthropic API key from https://console.anthropic.com/")
    
    print("\n🐳 Docker Services:")
    docker_services = ["postgres", "redis", "milvus-standalone"]
    
    for service in docker_services:
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service}", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )
            running = service in result.stdout
            print(f"  {check_mark(running)} {service}")
            if not running:
                issues.append(f"Start {service}: docker-compose up -d {service}")
                all_good = False
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  {check_mark(False)} {service} - Docker not available")
            issues.append("Install Docker and run: docker-compose up -d")
            all_good = False
    
    print("\n📁 Project Structure:")
    required_dirs = [
        "src/a3e/core",
        "src/a3e/api/routes", 
        "src/a3e/services",
        "templates",
        "web",
        "migrations"
    ]
    
    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        print(f"  {check_mark(exists)} {dir_path}")
        if not exists:
            issues.append(f"Missing directory: {dir_path}")
            all_good = False
    
    print("\n🌐 Network Connectivity:")
    
    # Test external APIs
    try:
        import requests
        apis_to_test = [
            ("OpenAI", "https://api.openai.com/v1/models"),
            ("Anthropic", "https://api.anthropic.com/v1/messages"),
            ("Canvas", os.getenv("CANVAS_API_BASE", "https://canvas.instructure.com/api/v1")),
        ]
        
        for name, url in apis_to_test:
            try:
                response = requests.get(url, timeout=5)
                # 401/403 is OK - means API is reachable
                reachable = response.status_code in [200, 401, 403]
                print(f"  {check_mark(reachable)} {name} API")
                if not reachable:
                    issues.append(f"Check {name} API connectivity")
            except requests.RequestException:
                print(f"  {check_mark(False)} {name} API - Connection failed")
                issues.append(f"Check internet connection to {name}")
    except ImportError:
        print("  ⚠️  Cannot test APIs - requests module missing")
    
    print("\n" + "="*50)
    
    if all_good and not issues:
        print("🎉 System Status: ALL GOOD!")
        print("✅ Ready to run: python -m uvicorn src.a3e.main:app --reload")
    else:
        print("⚠️  System Status: ISSUES FOUND")
        print("\n🔧 Action Items:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n💡 Quick Fixes:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Start services: docker-compose up -d")
        print("  • Check .env file configuration")
        print("  • Run health check again: python health_check.py")
    
    return all_good

if __name__ == "__main__":
    try:
        healthy = run_health_check()
        sys.exit(0 if healthy else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Health check cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        sys.exit(1)
