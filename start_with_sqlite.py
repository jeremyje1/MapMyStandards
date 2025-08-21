#!/usr/bin/env python3
"""
Start the app with SQLite for testing while PostgreSQL is being fixed
"""

import os
import sys

# Force SQLite for now
os.environ["DATABASE_URL"] = "sqlite:///./a3e_temp.db"
os.environ["ENVIRONMENT"] = "production"

# Ensure other required variables are set
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "temporary-dev-key-change-in-production"
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "temporary-dev-key-change-in-production"

print("🚀 Starting A3E with SQLite (temporary)")
print(f"Database: {os.environ['DATABASE_URL']}")

# Import and run
from src.a3e.main_production import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
