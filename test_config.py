#!/usr/bin/env python3
"""
Test the config loading with simplified settings.
"""
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set simple environment variables
os.environ['ENVIRONMENT'] = 'development'
os.environ['DEBUG'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['LLM_PROVIDER'] = 'openai'
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['SUPPORTED_FILE_TYPES'] = 'pdf,docx,xlsx,csv,txt,md'
os.environ['CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:8000'

try:
    from a3e.core.config import Settings
    settings = Settings()
    print("✅ Settings loaded successfully")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Supported file types: {settings.supported_file_types}")
    print(f"Supported file types (list): {settings.supported_file_types_list}")
    print(f"CORS origins: {settings.cors_origins}")
    print(f"CORS origins (list): {settings.cors_origins_list}")
except Exception as e:
    print(f"❌ Config loading failed: {e}")
    import traceback
    traceback.print_exc()
