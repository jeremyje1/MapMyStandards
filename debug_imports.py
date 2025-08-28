#!/usr/bin/env python3
"""
Debug script to identify which imports are failing in src.a3e.main
"""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name}")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False

def main():
    print("=== Import Debugging Session ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {sys.path[0]}")
    
    # Test basic imports first
    test_import("fastapi", "FastAPI framework")
    test_import("uvicorn", "UVICORN server")
    test_import("sqlalchemy", "SQLAlchemy ORM")
    test_import("pydantic", "Pydantic models")
    
    # Test our package structure
    test_import("src", "Source package")
    test_import("src.a3e", "A3E package")
    
    # Test config first (dependency for others)
    config_ok = test_import("src.a3e.core.config", "Config module")
    
    if config_ok:
        try:
            from src.a3e.core.config import settings
            print(f"✅ Settings loaded: environment={getattr(settings, 'environment', 'unknown')}")
        except Exception as e:
            print(f"❌ Settings instantiation failed: {e}")
    
    # Test database models
    test_import("src.a3e.database.models", "Database models")
    test_import("src.a3e.database.connection", "Database connection")
    
    # Test services
    test_import("src.a3e.services.database_service", "Database service")
    test_import("src.a3e.services.llm_service", "LLM service") 
    test_import("src.a3e.services.document_service", "Document service")
    
    # Test core modules
    test_import("src.a3e.core.accreditation_registry", "Accreditation registry")
    test_import("src.a3e.models", "Main models")
    
    # Test API routers
    test_import("src.a3e.api", "API package")
    test_import("src.a3e.api.routes.billing", "Billing router")
    
    # Finally test main module
    print("\n=== Testing main application ===")
    try:
        import src.a3e.main
        print("✅ Main application imported successfully!")
    except Exception as e:
        print(f"❌ Main application import failed: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()