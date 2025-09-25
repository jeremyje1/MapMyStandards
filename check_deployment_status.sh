#!/bin/bash
# Check Railway deployment status

echo "🔍 Checking Railway deployment status..."
echo ""

# Test the new endpoints
echo "Testing new API endpoints:"
echo ""

# Get auth token if available
TOKEN=$(cat ~/.a3e_token 2>/dev/null || echo "")

# Test document list endpoint
echo "1. Testing /documents/list endpoint..."
if [ -n "$TOKEN" ]; then
    curl -s -o /dev/null -w "   Status: %{http_code}\n" \
        -H "Authorization: Bearer $TOKEN" \
        "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/list"
else
    echo "   ⚠️  No auth token found, skipping authenticated test"
fi

# Test delete endpoint (without actually deleting)
echo ""
echo "2. Testing DELETE /documents/{id} endpoint exists..."
curl -s -o /dev/null -w "   Status: %{http_code} (expected 404 for fake ID)\n" \
    -X DELETE \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/test-id-123"

# Test analyze endpoint
echo ""
echo "3. Testing POST /documents/{id}/analyze endpoint exists..."
curl -s -o /dev/null -w "   Status: %{http_code} (expected 404 for fake ID)\n" \
    -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/test-id-123/analyze"

# Test dashboard endpoints
echo ""
echo "4. Testing dashboard endpoints..."
echo "   /documents/recent:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/recent"

echo "   /compliance/summary:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/compliance/summary"

echo "   /risk/summary:"
curl -s -o /dev/null -w "   Status: %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    "https://api.mapmystandards.ai/api/user/intelligence-simple/risk/summary"

echo ""
echo "✅ If you see 401/403 instead of 404, the endpoints exist!"
echo "✅ If you see 200, the endpoints are working!"
echo "❌ If you see 404 for all, deployment hasn't updated yet"