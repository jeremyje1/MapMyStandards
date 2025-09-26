#!/usr/bin/env python3
import jwt
import datetime

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJzdWIiOiJqZXN0cmVsbGFraXNzLmlAZ21haWwuY29tIiwidXNlcl9pZCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJleHAiOjE3NjYxNjA1NDB9.uFJhBYJ8GJgdOovASxQfgr4LJtq7j9zx3g9mRhE0IjQ"

# Decode without verification to check contents
try:
    claims = jwt.decode(token, options={"verify_signature": False})
    print("Token contents:")
    for key, value in claims.items():
        if key == "exp":
            exp_time = datetime.datetime.fromtimestamp(value)
            print(f"  {key}: {value} ({exp_time})")
            print(f"  Expired: {exp_time < datetime.datetime.now()}")
        else:
            print(f"  {key}: {value}")
except Exception as e:
    print(f"Error decoding token: {e}")