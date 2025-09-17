#!/bin/bash

# Extended deployment health check for MapMyStandards API
# Verifies all key endpoints are functioning correctly
# Usage: ./check_deployment_extended.sh [BASE_URL] [AUTH_TOKEN]

set -e

# Configuration
BASE_URL=${1:-${TARGET_URL:-https://api.mapmystandards.ai}}
AUTH_TOKEN=${2:-${MMS_AUTH_TOKEN:-}}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Extended Deployment Health Check"
echo "====================================="
echo "API Base: ${BASE_URL}"
echo "Time: $(date)"
echo ""

# Track overall status
ALL_GOOD=true

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected=$2
    local description=$3
    local auth_required=${4:-false}
    
    local headers=""
    if [ "$auth_required" = true ] && [ -n "$AUTH_TOKEN" ]; then
        headers="-H \"Authorization: Bearer ${AUTH_TOKEN}\""
    fi
    
    # Make request with eval to handle dynamic headers
    if [ -n "$headers" ]; then
        response=$(eval "curl -s -o /dev/null -w \"%{http_code}\" $headers \"${BASE_URL}${endpoint}\"")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${endpoint}")
    fi
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} ${description}: ${response} (${endpoint})"
        return 0
    else
        echo -e "${RED}✗${NC} ${description}: ${response} (expected ${expected}) (${endpoint})"
        ALL_GOOD=false
        return 1
    fi
}

# Function to check endpoint with data validation
check_endpoint_data() {
    local endpoint=$1
    local description=$2
    local auth_required=${3:-false}
    
    local headers=""
    if [ "$auth_required" = true ] && [ -n "$AUTH_TOKEN" ]; then
        headers="-H \"Authorization: Bearer ${AUTH_TOKEN}\""
    fi
    
    # Make request and capture both status and body
    if [ -n "$headers" ]; then
        response=$(eval "curl -s -w \"\\n%{http_code}\" $headers \"${BASE_URL}${endpoint}\"")
    else
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}")
    fi
    
    # Split response into body and status code
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        # Check if body contains data (not empty JSON)
        if echo "$body" | grep -q '"data"\|"standards"\|"accreditor"\|"metrics"\|"status"' 2>/dev/null; then
            echo -e "${GREEN}✓${NC} ${description}: 200 with data (${endpoint})"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} ${description}: 200 but empty/unexpected response (${endpoint})"
            ALL_GOOD=false
            return 1
        fi
    else
        echo -e "${RED}✗${NC} ${description}: ${http_code} (${endpoint})"
        ALL_GOOD=false
        return 1
    fi
}

echo "1. Basic Health Checks"
echo "----------------------"
check_endpoint "/health" "200" "API Health"
check_endpoint "/" "200" "Root Endpoint"
check_endpoint "/docs" "200" "API Documentation"
check_endpoint "/health/frontend" "200" "Frontend Health"

echo ""
echo "2. Public Endpoints"
echo "-------------------"
check_endpoint_data "/api/user/intelligence-simple/standards/metadata" "Standards Metadata"

echo ""
echo "3. Authentication Endpoints"
echo "---------------------------"
# These might require different handling in production
check_endpoint "/api/auth/login" "405" "Auth Login (Method Check)"
check_endpoint "/api/v1/billing/config/stripe-key" "200" "Stripe Configuration"

if [ -n "$AUTH_TOKEN" ]; then
    echo ""
    echo "4. Protected Endpoints (with auth)"
    echo "----------------------------------"
    check_endpoint_data "/api/user/intelligence-simple/standards/list" "Standards List" true
    check_endpoint_data "/api/user/intelligence-simple/standards/evidence-map" "Evidence Mapping" true
    check_endpoint "/api/user/intelligence-simple/dashboard/overview" "200" "Dashboard Overview" true
    check_endpoint "/api/user/intelligence-simple/reports" "200" "Reports Endpoint" true
    check_endpoint_data "/api/user/intelligence-simple/risk/factors" "Risk Factors" true
    check_endpoint "/api/user/intelligence-simple/settings" "200" "User Settings" true
else
    echo ""
    echo "4. Protected Endpoints"
    echo "----------------------"
    echo -e "${YELLOW}⚠${NC} Skipping authenticated endpoints (no AUTH_TOKEN provided)"
    echo "   To test authenticated endpoints, run:"
    echo "   AUTH_TOKEN=<your-token> $0 $BASE_URL"
fi

echo ""
echo "5. Upload & Processing"
echo "----------------------"
# Check if upload endpoint exists (might need auth)
if [ -n "$AUTH_TOKEN" ]; then
    check_endpoint "/api/user/intelligence-simple/evidence/upload" "405" "Upload Endpoint (Method Check)" true
else
    check_endpoint "/api/user/intelligence-simple/evidence/upload" "401" "Upload Endpoint (Auth Required)"
fi

echo ""
echo "6. Standards Cross-References"
echo "-----------------------------"
# Test cross-accreditor matching with parameters
if curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/user/intelligence-simple/standards/cross-accreditor-matches?source=HLC&target=MSCHE" | grep -q "200\|401"; then
    echo -e "${GREEN}✓${NC} Cross-accreditor matching endpoint available"
else
    echo -e "${RED}✗${NC} Cross-accreditor matching endpoint not available"
    ALL_GOOD=false
fi

echo ""
echo "7. API Performance"
echo "------------------"
# Measure response time for health endpoint
start_time=$(date +%s%N)
curl -s -o /dev/null "${BASE_URL}/health"
end_time=$(date +%s%N)
elapsed=$((($end_time - $start_time) / 1000000)) # Convert to milliseconds

if [ $elapsed -lt 1000 ]; then
    echo -e "${GREEN}✓${NC} Health check response time: ${elapsed}ms"
elif [ $elapsed -lt 3000 ]; then
    echo -e "${YELLOW}⚠${NC} Health check response time: ${elapsed}ms (slow)"
else
    echo -e "${RED}✗${NC} Health check response time: ${elapsed}ms (very slow)"
    ALL_GOOD=false
fi

echo ""
echo "====================================="
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "Deployment is healthy and ready for use."
    exit 0
else
    echo -e "${RED}✗ Some checks failed!${NC}"
    echo "Please review the failures above and check application logs."
    exit 1
fi