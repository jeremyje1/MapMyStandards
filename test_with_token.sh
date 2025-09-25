#!/bin/bash
# Test endpoints with a real token

echo "To test the endpoints with authentication:"
echo ""
echo "1. Open browser console at https://platform.mapmystandards.ai/upload-working.html"
echo "2. Run: localStorage.getItem('access_token')"
echo "3. Copy the token (without quotes)"
echo "4. Run this command with your token:"
echo ""
echo "   TOKEN='your-token-here' ./test_with_token.sh"
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ No TOKEN provided. Set TOKEN environment variable first."
    exit 1
fi

echo "Testing with provided token..."
echo ""

# Test document list
echo "1. GET /documents/list:"
curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/list" | jq '.'

echo ""
echo "2. GET /documents/recent:"
curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/recent" | jq '.'

echo ""
echo "3. GET /compliance/summary:"
curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/compliance/summary" | jq '.'