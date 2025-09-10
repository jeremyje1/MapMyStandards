#!/usr/bin/env python3
"""
Test the User Intelligence API endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import jwt

# Configuration
BASE_URL = "http://localhost:8000"
JWT_SECRET = "test-jwt-key"

# Create a test JWT token
def create_test_token(email="test@example.com"):
    """Create a test JWT token"""
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def test_dashboard_overview():
    """Test the dashboard overview endpoint"""
    token = create_test_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/user/intelligence/dashboard/overview",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Response:", json.dumps(response.json(), indent=2))
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    print("Testing User Intelligence API...")
    test_dashboard_overview()
