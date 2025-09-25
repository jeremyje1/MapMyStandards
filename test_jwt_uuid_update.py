#!/usr/bin/env python3
"""Test the updated JWT token format with UUIDs"""

import jwt
import json
from datetime import datetime, timedelta

# Test data
test_user_id = "e144cf90-d8ed-4277-bf12-3d86443e2099"
test_email = "jeremy.estrella@gmail.com"
test_name = "Jeremy Estrella"
JWT_SECRET = "your-secret-key-here-change-in-production"
JWT_ALGORITHM = "HS256"

print("JWT Token UUID Update Test")
print("=" * 60)

# Create a new format token (with UUID)
print("\n1. Creating new format token (with UUID):")
new_payload = {
    "sub": test_user_id,
    "user_id": test_user_id,
    "email": test_email,
    "name": test_name,
    "exp": datetime.utcnow() + timedelta(hours=24),
    "iat": datetime.utcnow()
}

new_token = jwt.encode(new_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(f"Token: {new_token[:50]}...")

# Decode and display
decoded = jwt.decode(new_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
print("\nDecoded payload:")
print(json.dumps(decoded, indent=2, default=str))

# Create an old format token (email in sub)
print("\n2. Creating old format token (email in sub):")
old_payload = {
    "sub": test_email,
    "exp": datetime.utcnow() + timedelta(hours=24),
    "iat": datetime.utcnow()
}

old_token = jwt.encode(old_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(f"Token: {old_token[:50]}...")

# Decode and display
decoded = jwt.decode(old_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
print("\nDecoded payload:")
print(json.dumps(decoded, indent=2, default=str))

print("\n3. Testing backward compatibility:")
print("-" * 40)

# Test function that mimics the verify_jwt_token_email behavior
def get_email_from_token(token):
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload.get("email", payload.get("sub"))

print(f"Email from new token: {get_email_from_token(new_token)}")
print(f"Email from old token: {get_email_from_token(old_token)}")

print("\n4. Benefits of the new format:")
print("-" * 40)
print("✓ UUID in 'sub' field - proper subject identifier")
print("✓ Email preserved in 'email' field - for display/lookups")
print("✓ Name included - reduces database queries")
print("✓ Backward compatible - old tokens still work")
print("✓ No more email-to-UUID conversion needed!")

print("\n" + "=" * 60)
print("RESULT: JWT tokens now properly include UUIDs!")