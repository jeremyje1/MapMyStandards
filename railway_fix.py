#!/usr/bin/env python3
"""
Quick fix for Railway deployment
Creates required directories and ensures proper startup
"""

import os
from pathlib import Path

def ensure_directories():
    """Create required directories for Railway deployment"""
    directories = [
        "jobs_status",
        "reports_generated", 
        "uploads",
        "web/static/css"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
        
        # Create .gitkeep to ensure directory exists in git
        gitkeep = Path(directory) / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"✅ Added .gitkeep to: {directory}")

def fix_railway_startup():
    """Ensure Railway startup works correctly"""
    # Set environment variables for Railway
    os.environ.setdefault("PYTHONPATH", "/app")
    os.environ.setdefault("FEATURE_DEMO_MODE", "true")
    
    print("✅ Environment configured for Railway")
    
if __name__ == "__main__":
    print("🔧 Railway Fix Script")
    print("=" * 30)
    
    ensure_directories()
    fix_railway_startup()
    
    print("\n🎉 Railway fix complete!")
    print("💡 Run this before deployment to ensure directories exist")