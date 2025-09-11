#!/usr/bin/env python3
"""
Production JWT Token Generator for Dashboard Access
Uses production-level secret key for secure token generation
"""

import jwt
from datetime import datetime, timedelta

# Production secret key (same as deployed to Railway/Vercel)
PRODUCTION_SECRET_KEY = "BzKxm0pmrXyEyJditsbVDnngbvyhD512-xo0ei5G_l-si4m4B4dsE7DQeF9zYduD1-AtYvvIK-v1fAXS7QjFWQ"
JWT_ALGORITHM = "HS256"

def generate_production_token():
    """Generate a JWT token for production dashboard access"""
    
    # Token payload
    payload = {
        "sub": "production@mapmystandards.ai",
        "email": "production@mapmystandards.ai", 
        "user_id": "production-user-001",
        "exp": datetime.utcnow() + timedelta(days=30),  # 30-day expiration for production
        "iat": datetime.utcnow(),
        "environment": "production"
    }
    
    # Generate token
    token = jwt.encode(payload, PRODUCTION_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token

if __name__ == "__main__":
    print("🔑 Production JWT Token Generator")
    print("=" * 50)
    
    # Generate the token
    production_token = generate_production_token()
    
    print("✅ Production JWT Token Generated!")
    print()
    print("📋 Token (copy this entire string):")
    print(production_token)
    print()
    print("🌐 localStorage Setup Command:")
    print(f"localStorage.setItem('jwt_token', '{production_token}');")
    print()
    print("📝 Instructions:")
    print("1. Open your browser's Developer Console (F12)")
    print("2. Paste the localStorage command above")
    print("3. Press Enter to execute")
    print("4. Navigate to your dashboard - authentication will work automatically")
    print()
    print("⏱️  Token expires in 30 days")
    print("🔒 Uses production-grade secret key")
    print("🌍 Compatible with Railway & Vercel deployments")
