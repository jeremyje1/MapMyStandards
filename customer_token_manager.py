#!/usr/bin/env python3
"""
Customer JWT Token Management System
Secure token generation for MapMyStandards dashboard access
"""

import jwt
import os
import sys
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

JWT_ALGORITHM = "HS256"

def get_secret_key():
    """Get JWT secret key from environment variable"""
    secret = os.getenv('JWT_SECRET_KEY')
    if not secret:
        print("❌ Error: JWT_SECRET_KEY environment variable not set")
        print("Please set it with: export JWT_SECRET_KEY='your-secret-key'")
        sys.exit(1)
    return secret

def generate_customer_token(
    customer_email: str,
    customer_org: str,
    days_valid: int = 30,
    tier: str = "standard"
) -> str:
    """Generate a JWT token for a specific customer"""
    
    # Validate inputs
    if not customer_email or "@" not in customer_email:
        raise ValueError("Valid customer email required")
    
    if not customer_org:
        raise ValueError("Customer organization name required")
    
    # Generate unique customer ID
    customer_id = hashlib.sha256(f"{customer_email}:{customer_org}".encode()).hexdigest()[:16]
    
    # Token payload with customer-specific data
    payload = {
        "sub": customer_email,
        "email": customer_email,
        "user_id": f"customer-{customer_id}",
        "organization": customer_org,
        "tier": tier,
        "exp": datetime.utcnow() + timedelta(days=days_valid),
        "iat": datetime.utcnow(),
        "environment": "production",
        "token_version": "1.0"
    }
    
    # Generate token with environment secret
    secret_key = get_secret_key()
    token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    
    return token

def validate_token(token: str) -> Optional[dict]:
    """Validate a JWT token and return payload if valid"""
    try:
        secret_key = get_secret_key()
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

def main():
    print("🔑 MapMyStandards Customer Token Manager")
    print("=" * 50)
    
    # Check if this is token validation
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        if len(sys.argv) < 3:
            print("Usage: python3 customer_token_manager.py validate <token>")
            sys.exit(1)
        
        token = sys.argv[2]
        result = validate_token(token)
        
        if "error" in result:
            print(f"❌ Token validation failed: {result['error']}")
        else:
            print("✅ Token is valid!")
            print(f"Customer: {result.get('email')}")
            print(f"Organization: {result.get('organization')}")
            print(f"Tier: {result.get('tier')}")
            print(f"Expires: {datetime.fromtimestamp(result.get('exp'))}")
        return
    
    # Interactive token generation
    print("Please provide customer information:")
    print()
    
    customer_email = input("Customer Email: ").strip()
    customer_org = input("Organization Name: ").strip()
    
    print()
    print("Token Duration Options:")
    print("1. 7 days (trial)")
    print("2. 30 days (standard)")
    print("3. 90 days (premium)")
    print("4. 365 days (enterprise)")
    
    duration_choice = input("Select duration (1-4): ").strip()
    
    duration_map = {
        "1": (7, "trial"),
        "2": (30, "standard"), 
        "3": (90, "premium"),
        "4": (365, "enterprise")
    }
    
    if duration_choice not in duration_map:
        print("❌ Invalid choice. Using 30 days (standard)")
        days_valid, tier = 30, "standard"
    else:
        days_valid, tier = duration_map[duration_choice]
    
    try:
        # Generate the token
        token = generate_customer_token(customer_email, customer_org, days_valid, tier)
        
        print()
        print("✅ Customer JWT Token Generated!")
        print("=" * 50)
        print(f"📧 Customer: {customer_email}")
        print(f"🏢 Organization: {customer_org}")
        print(f"🎯 Tier: {tier}")
        print(f"⏱️  Valid for: {days_valid} days")
        print()
        print("📋 Token (provide this to customer):")
        print(token)
        print()
        print("🌐 Customer Setup Instructions:")
        print("Tell your customer to:")
        print("1. Open their browser's Developer Console (F12)")
        print("2. Go to the Console tab")
        print("3. Paste this command:")
        print(f"   localStorage.setItem('jwt_token', '{token}');")
        print("4. Press Enter")
        print("5. Navigate to the dashboard")
        print()
        print("🔒 Security Notes:")
        print("- This token is unique to this customer")
        print("- It cannot be used by other customers")
        print("- You can validate it anytime with:")
        print(f"  python3 {sys.argv[0]} validate {token}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
