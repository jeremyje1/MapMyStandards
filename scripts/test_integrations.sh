#!/bin/bash

# Integration Testing Script for A³E
# Tests all integrations and configurations

set -e

echo "🧪 A³E Integration Testing Suite"
echo "================================="
echo ""

BASE_URL="http://localhost:8000"
if [ "$1" = "prod" ]; then
    BASE_URL="https://api.mapmystandards.ai"
    echo "🌐 Testing production environment: $BASE_URL"
else
    echo "🏠 Testing local environment: $BASE_URL"
fi

echo ""

# Test basic API health
echo "1. Testing API Health..."
if curl -s -f "$BASE_URL/health" > /dev/null; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    exit 1
fi

# Test API root
echo ""
echo "2. Testing API Root..."
API_INFO=$(curl -s "$BASE_URL/" | python3 -m json.tool 2>/dev/null || echo "Failed to parse JSON")
if echo "$API_INFO" | grep -q "A3E"; then
    echo "✅ API root endpoint working"
    echo "   $(echo "$API_INFO" | grep '"message"' | cut -d'"' -f4)"
else
    echo "❌ API root endpoint failed"
fi

# Test configuration endpoints
echo ""
echo "3. Testing Configuration Endpoints..."

# Test accreditors
ACCREDITORS=$(curl -s "$BASE_URL/api/v1/config/accreditors")
if echo "$ACCREDITORS" | grep -q "SACSCOC\|NECHE\|WSCUC"; then
    echo "✅ Accreditors configuration loaded"
    ACCREDITOR_COUNT=$(echo "$ACCREDITORS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Found $ACCREDITOR_COUNT accreditors"
else
    echo "❌ Accreditors configuration failed"
fi

# Test institution types
INST_TYPES=$(curl -s "$BASE_URL/api/v1/config/institution-types")
if echo "$INST_TYPES" | grep -q "university\|college"; then
    echo "✅ Institution types configuration loaded"
else
    echo "❌ Institution types configuration failed"
fi

# Test evidence tags
EVIDENCE_TAGS=$(curl -s "$BASE_URL/api/v1/config/evidence-tags")
if echo "$EVIDENCE_TAGS" | grep -q "student_learning_outcomes\|faculty_credentials"; then
    echo "✅ Evidence tags configuration loaded"
else
    echo "❌ Evidence tags configuration failed"
fi

# Test integration status
echo ""
echo "4. Testing Integration Status..."
INTEGRATION_STATUS=$(curl -s "$BASE_URL/api/v1/integrations/status")
if echo "$INTEGRATION_STATUS" | grep -q "integrations"; then
    echo "✅ Integration status endpoint working"
    
    # Parse integration status
    CANVAS_CONFIGURED=$(echo "$INTEGRATION_STATUS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['integrations']['canvas']['configured'])" 2>/dev/null || echo "false")
    BANNER_CONFIGURED=$(echo "$INTEGRATION_STATUS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['integrations']['banner']['configured'])" 2>/dev/null || echo "false")
    SHAREPOINT_CONFIGURED=$(echo "$INTEGRATION_STATUS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['integrations']['sharepoint']['configured'])" 2>/dev/null || echo "false")
    
    echo "   Canvas: $CANVAS_CONFIGURED"
    echo "   Banner: $BANNER_CONFIGURED" 
    echo "   SharePoint: $SHAREPOINT_CONFIGURED"
else
    echo "❌ Integration status endpoint failed"
fi

# Test specific accreditor details
echo ""
echo "5. Testing Specific Accreditor Details..."
SACSCOC_DETAILS=$(curl -s "$BASE_URL/api/v1/config/accreditors/sacscoc")
if echo "$SACSCOC_DETAILS" | grep -q "Southern Association"; then
    echo "✅ SACSCOC details loaded correctly"
    STANDARDS_COUNT=$(echo "$SACSCOC_DETAILS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['standards']))" 2>/dev/null || echo "0")
    echo "   Found $STANDARDS_COUNT SACSCOC standards"
else
    echo "❌ SACSCOC details failed"
fi

# Test standards search
echo ""
echo "6. Testing Standards Search..."
SEARCH_RESULTS=$(curl -s "$BASE_URL/api/v1/config/search/standards?keyword=mission")
if echo "$SEARCH_RESULTS" | grep -q "mission\|Mission"; then
    echo "✅ Standards search working"
    RESULTS_COUNT=$(echo "$SEARCH_RESULTS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Found $RESULTS_COUNT results for 'mission'"
else
    echo "❌ Standards search failed"
fi

# Test evidence classification
echo ""
echo "7. Testing Evidence Classification..."
CLASSIFICATION_RESULT=$(curl -s -X POST "$BASE_URL/api/v1/config/evidence/classify" \
    -H "Content-Type: application/json" \
    -d '"This document contains student learning outcomes and assessment data for our business program."')
if echo "$CLASSIFICATION_RESULT" | grep -q "student_learning_outcomes"; then
    echo "✅ Evidence classification working"
    TAGS_COUNT=$(echo "$CLASSIFICATION_RESULT" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Classified into $TAGS_COUNT evidence tags"
else
    echo "❌ Evidence classification failed"
fi

# Test institutions endpoint
echo ""
echo "8. Testing Institutions Endpoint..."
INSTITUTIONS=$(curl -s "$BASE_URL/api/v1/institutions")
if echo "$INSTITUTIONS" | grep -q "\[\]" || echo "$INSTITUTIONS" | grep -q "id.*name"; then
    echo "✅ Institutions endpoint working"
else
    echo "❌ Institutions endpoint failed"
fi

# Test OpenAPI documentation
echo ""
echo "9. Testing API Documentation..."
if curl -s -f "$BASE_URL/docs" > /dev/null; then
    echo "✅ API documentation accessible"
else
    echo "❌ API documentation not accessible"
fi

# Test database connectivity (local only)
if [ "$1" != "prod" ]; then
    echo ""
    echo "10. Testing Database Connectivity..."
    if docker-compose exec -T postgres psql -U a3e -d a3e -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ Database connection working"
    else
        echo "❌ Database connection failed"
    fi
fi

# Performance test
echo ""
echo "11. Performance Test..."
start_time=$(date +%s%3N)
curl -s "$BASE_URL/api/v1/config/accreditors" > /dev/null
end_time=$(date +%s%3N)
response_time=$((end_time - start_time))

if [ $response_time -lt 1000 ]; then
    echo "✅ Response time: ${response_time}ms (excellent)"
elif [ $response_time -lt 2000 ]; then
    echo "⚠️  Response time: ${response_time}ms (good)"
else
    echo "❌ Response time: ${response_time}ms (slow)"
fi

# SSL test (production only)
if [ "$1" = "prod" ]; then
    echo ""
    echo "12. Testing SSL Certificate..."
    SSL_INFO=$(echo | openssl s_client -connect api.mapmystandards.ai:443 -servername api.mapmystandards.ai 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if echo "$SSL_INFO" | grep -q "notAfter"; then
        echo "✅ SSL certificate valid"
        echo "   $SSL_INFO"
    else
        echo "❌ SSL certificate check failed"
    fi
fi

echo ""
echo "📊 Test Summary"
echo "==============="

# Count results
TOTAL_TESTS=11
if [ "$1" = "prod" ]; then
    TOTAL_TESTS=12
fi

PASSED_TESTS=$(grep -c "✅" <<< "$(cat)")
echo "Passed: $PASSED_TESTS"
echo "Total:  $TOTAL_TESTS"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo ""
    echo "🎉 All tests passed! A³E is ready for production."
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Please check the configuration."
    exit 1
fi
