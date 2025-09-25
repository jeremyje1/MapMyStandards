#!/usr/bin/env python3
"""Debug JWT verification to see why tokens are failing"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import after path setup
from a3e.core.config import get_settings

print("JWT Verification Debug")
print("=" * 60)

# Check environment variables
env_vars = [
    "JWT_SECRET_KEY",
    "JWT_SECRET",
    "SECRET_KEY",
    "ONBOARDING_SHARED_SECRET"
]

print("\nEnvironment Variables:")
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"  {var}: {'*' * 10} (set)")
    else:
        print(f"  {var}: (not set)")

# Check settings
try:
    settings = get_settings()
    print("\nSettings object:")
    print(f"  jwt_secret_key: {'*' * 10 if hasattr(settings, 'jwt_secret_key') and settings.jwt_secret_key else '(not set)'}")
    print(f"  secret_key: {'*' * 10 if hasattr(settings, 'secret_key') and settings.secret_key else '(not set)'}")
except Exception as e:
    print(f"\nError loading settings: {e}")

# Import the verification function
try:
    from a3e.api.routes.user_intelligence_simple import _candidate_secrets
    secrets = _candidate_secrets()
    print(f"\nCandidate secrets found: {len(secrets)}")
    for i, secret in enumerate(secrets):
        print(f"  Secret {i+1}: {'*' * 10} (length: {len(secret)})")
except Exception as e:
    print(f"\nError getting candidate secrets: {e}")

print("\n" + "=" * 60)
print("Note: If no environment variables are set locally,")
print("the production deployment on Railway should have JWT_SECRET_KEY set.")