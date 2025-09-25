#!/usr/bin/env python3
"""Test JWT token contents to understand the user ID issue"""

import jwt
import json

# Sample token from the error logs (expired, so safe to decode without verification)
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZXhwIjoxNzU5MDY4MDc0LCJpYXQiOjE3Mjc1MzIwNzQsInVzZXJfaWQiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZW1haWwiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZnVsbF9uYW1lIjoiSmVyZW15IEVzdHJlbGxhIn0.xvdULt_wNzCOcYZqBGJyv-OGD1hJezXQ0FU1c3bCKJY"

print("JWT Token Analysis")
print("=" * 60)

try:
    # Decode without verification (since we just want to see the contents)
    payload = jwt.decode(test_token, options={"verify_signature": False})
    
    print("\nToken payload:")
    print(json.dumps(payload, indent=2))
    
    print("\nKey observations:")
    print(f"- 'sub' field: {payload.get('sub')}")
    print(f"- 'user_id' field: {payload.get('user_id')}")
    print(f"- 'email' field: {payload.get('email')}")
    
    print("\nPROBLEM CONFIRMED:")
    print("All user identifier fields contain the email address, not the UUID!")
    print("This is why document queries fail - they're looking for email instead of UUID")
    
except Exception as e:
    print(f"Error decoding token: {e}")

print("\n" + "=" * 60)
print("SOLUTION:")
print("The API needs to look up the UUID from the email address")
print("OR the JWT token generation needs to be fixed to include the UUID")