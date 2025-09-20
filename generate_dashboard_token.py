#!/usr/bin/env python3
"""JWT Dashboard Token Generator and Setter

Generates a JWT compatible with the backend simple auth verifier.
IMPORTANT: Backend decodes with SECRET_KEY (see src/a3e/api/dependencies.py).
This script prefers SECRET_KEY to ensure compatibility; you can override with TOKEN_SECRET.
Includes customer claims so the dashboard is tailored (no demo data).
"""

import os
import jwt
import json
from datetime import datetime, timedelta

# Choose a signing secret that matches the backend verifier
# Order of precedence: TOKEN_SECRET (explicit override) -> SECRET_KEY -> JWT_SECRET_KEY -> ONBOARDING_SHARED_SECRET -> dev fallback
SECRET_KEY = os.getenv("TOKEN_SECRET") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or os.getenv("ONBOARDING_SHARED_SECRET") or "dev-secret"
ALGORITHM = "HS256"

def create_dashboard_token():
    """Create a JWT token for dashboard access with customer-tailoring claims"""
    # Claims (can be overridden via environment for quick testing)
    email = os.getenv("TEST_USER_EMAIL", "test@example.com")
    org = os.getenv("ORG_NAME", "")
    tier = os.getenv("TIER", "standard")
    # Plan/subscription claims used by access gating on some endpoints
    plan = os.getenv("PLAN", "professional")  # professional | trial | enterprise
    subscription_status = os.getenv("SUBSCRIPTION_STATUS")  # e.g., active | past_due | canceled
    trial_status = os.getenv("TRIAL_STATUS")  # e.g., active | expired
    name = os.getenv("NAME")
    accreditor = os.getenv("PRIMARY_ACCREDITOR", "")

    payload = {
        "sub": email,
        "email": email,
        "user_id": os.getenv("USER_ID", "test-user-123"),
        "organization": org,
        "tier": tier,
        "plan": plan,
        **({"subscription_status": subscription_status} if subscription_status else {}),
        **({"trial_status": trial_status} if trial_status else {}),
        **({"name": name} if name else {}),
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
    print("1) In your browser console (set across common keys):")
    print(f"   localStorage.setItem('jwt_token', '{token}');")
    print(f"   localStorage.setItem('access_token', '{token}');")
    print(f"   localStorage.setItem('a3e_api_key', '{token}');")
    print("2) Then open your app (e.g., http://localhost:8000/ai-dashboard)")
    print()
    print("🔐 Tip: Ensure the signing secret matches backend SECRET_KEY.")
    print("    You can set TOKEN_SECRET env var when running this script.")
    print()
    print("� This token includes claims: email, organization, tier, plan,")
    print("  (optional) subscription_status, trial_status, name, primary_accreditor")
    print("  Override with ORG_NAME, TIER, PLAN, SUBSCRIPTION_STATUS, TRIAL_STATUS,")
    print("  NAME, PRIMARY_ACCREDITOR env vars before running.")
    print()
    print("⏱️  Token expires in 7 days")

if __name__ == "__main__":
    main()
