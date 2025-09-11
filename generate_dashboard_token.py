#!/usr/bin/env python3
"""JWT Dashboard Token Generator and Setter"""

import jwt
import json
from datetime import datetime, timedelta

# Configuration matching current development environment
SECRET_KEY = "BzKxm0pmrXyEyJditsbVDnngbvyhD512-xo0ei5G_l-si4m4B4dsE7DQeF9zYduD1-AtYvvIK-v1fAXS7QjFWQ"
ALGORITHM = "HS256"

def create_dashboard_token():
    """Create a JWT token for dashboard access"""
    # Create token with long expiry for development
    payload = {
        "sub": "test@example.com",  # Email as subject
        "email": "test@example.com",
        "user_id": "test-user-123",
        "exp": datetime.utcnow() + timedelta(days=7),  # 7 days
        "iat": datetime.utcnow()
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
    print("1. Go to: http://localhost:8000/debug-api")
    print("2. Paste the token above in the 'JWT Token' field")
    print("3. Click 'Save Token'")
    print("4. Visit: http://localhost:8000/ai-dashboard")
    print()
    print("💻 OR use browser console:")
    print(f"localStorage.setItem('jwt_token', '{token}');")
    print("Then refresh the dashboard page")
    print()
    print("⏱️  Token expires in 7 days")

if __name__ == "__main__":
    main()
