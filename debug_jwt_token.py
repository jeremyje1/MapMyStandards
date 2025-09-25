#!/usr/bin/env python3
"""Debug JWT token contents"""

import jwt
import json
import base64
import sys

def decode_jwt_without_verification(token):
    """Decode JWT without verifying signature to see its contents"""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid token format")
            return None
        
        # Decode header
        header = base64.urlsafe_b64decode(parts[0] + '=' * (4 - len(parts[0]) % 4))
        print("Header:", json.loads(header))
        
        # Decode payload
        payload = base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
        payload_dict = json.loads(payload)
        print("\nPayload:")
        for key, value in payload_dict.items():
            print(f"  {key}: {value}")
        
        return payload_dict
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

# Instructions for the user
print("=" * 60)
print("JWT Token Debugger")
print("=" * 60)
print("\nTo debug your token:")
print("1. Open browser developer tools (F12)")
print("2. Go to Application/Storage > Cookies or Local Storage")
print("3. Find the token (might be in 'access_token', 'jwt_token', or 'a3e_api_key')")
print("4. Copy the token value")
print("5. Paste it below")
print("\nOr check the Network tab for Authorization headers in failed requests")
print("=" * 60)

if len(sys.argv) > 1:
    token = sys.argv[1]
else:
    token = input("\nPaste your JWT token here: ").strip()

if token:
    if token.startswith("Bearer "):
        token = token[7:]
    
    print("\n" + "=" * 60)
    decode_jwt_without_verification(token)
    print("\n" + "=" * 60)
    print("\nWhat to look for:")
    print("- 'sub' field: Should contain a UUID (not an email)")
    print("- 'user_id' field: Should also contain the UUID")
    print("- 'email' field: Should contain the email address")
    print("\nIf 'sub' contains an email instead of UUID, the token is outdated.")
    print("User needs to logout and login again to get a new token with UUID.")