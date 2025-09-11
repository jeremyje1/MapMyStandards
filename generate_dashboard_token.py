#!/usr/bin/env python3
"""JWT Dashboard Token Generator and Setter

Generates a token compatible with the backend simple auth verifier.
If ONBOARDING_SHARED_SECRET is set, uses it to match production onboarding tokens.
Includes customer claims so the dashboard is tailored (no demo data).
"""

import os
import jwt
import json
from datetime import datetime, timedelta

# Prefer onboarding shared secret for cross-environment compatibility
SECRET_KEY = os.getenv("ONBOARDING_SHARED_SECRET") or os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

def create_dashboard_token():
    """Create a JWT token for dashboard access with customer-tailoring claims"""
    # Claims (can be overridden via environment for quick testing)
    email = os.getenv("TEST_USER_EMAIL", "test@example.com")
    org = os.getenv("ORG_NAME", "")
    tier = os.getenv("TIER", "standard")
    accreditor = os.getenv("PRIMARY_ACCREDITOR", "")

    payload = {
        "sub": email,
        "email": email,
        "user_id": os.getenv("USER_ID", "test-user-123"),
        "organization": org,
        "tier": tier,
        # optional claim if available
        **({"primary_accreditor": accreditor} if accreditor else {}),
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def main():
    """Generate token and provide instructions"""
    print("🔑 JWT Dashboard Token Generator")
    print("=" * 50)
    
    # Generate token
    token = create_dashboard_token()
    
    print("✅ New JWT Token Generated!")
    print()
    print("📋 Token (copy this):")
    print(token)
    print()
    print("🌐 Dashboard Setup Instructions:")
    print("1. In your browser console:")
    print(f"   localStorage.setItem('jwt_token', '{token}');")
    print("2. Visit: http://localhost:8000/ai-dashboard")
    print()
    print("� This token includes claims: email, organization, tier, (optional) primary_accreditor")
    print("   Override with ORG_NAME, TIER, PRIMARY_ACCREDITOR env vars before running.")
    print()
    print("⏱️  Token expires in 7 days")

if __name__ == "__main__":
    main()
