#!/bin/bash

# Script to check CORS headers from the API

echo "Checking CORS headers from api.mapmystandards.ai..."
echo ""

# Check preflight request (OPTIONS)
echo "1. Testing OPTIONS request (CORS preflight):"
curl -I -X OPTIONS https://api.mapmystandards.ai/api/auth/login \
  -H "Origin: https://platform.mapmystandards.ai" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  2>/dev/null | grep -E "(Access-Control-|HTTP/)"

echo ""
echo "2. Testing GET request to /health endpoint:"
curl -I https://api.mapmystandards.ai/health \
  -H "Origin: https://platform.mapmystandards.ai" \
  2>/dev/null | grep -E "(Access-Control-|HTTP/)"

echo ""
echo "3. Testing POST request to /api/auth/login:"
curl -I -X POST https://api.mapmystandards.ai/api/auth/login \
  -H "Origin: https://platform.mapmystandards.ai" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}' \
  2>/dev/null | grep -E "(Access-Control-|HTTP/)"

echo ""
echo "If you see 'Access-Control-Allow-Origin' headers, CORS is configured correctly."
echo "If not, the CORS middleware may not be working properly."