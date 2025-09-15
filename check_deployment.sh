#!/bin/bash

# Monitor production deployment readiness
# Usage: ./check_deployment.sh [BASE_URL]
# - Reads BASE_URL from first arg or $TARGET_URL env var
# - Defaults to https://api.mapmystandards.ai

set -e

BASE_URL=${1:-${TARGET_URL:-https://api.mapmystandards.ai}}

echo "🔄 Monitoring deployment..."
echo "URL: ${BASE_URL}"
echo "Waiting for API to be ready (/health)..."
echo ""

start_time=$(date +%s)
max_wait=${MAX_WAIT_SECONDS:-300}  # default 5 minutes

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    if [ $elapsed -gt $max_wait ]; then
        echo ""
        echo "❌ Timeout waiting for deployment. Check platform logs."
        echo "   Tried: ${BASE_URL}/health"
        exit 1
    fi

    # Check health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")

    if [ "$response" = "200" ]; then
        echo ""
        echo "✅ API is healthy! Checking endpoints..."

        # Test key endpoints (public ones only)
        health_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
        root_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/")
        docs_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs")
        frontend_health_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health/frontend")

        echo "   Health: ${health_code} (${BASE_URL}/health)"
        echo "   Root:   ${root_code} (${BASE_URL}/)"
        echo "   Docs:   ${docs_code} (${BASE_URL}/docs)"
        echo "   FE HC:  ${frontend_health_code} (${BASE_URL}/health/frontend)"

        echo ""
        echo "🎉 Deployment verified!"
        echo "   Total wait time: ${elapsed} seconds"
        exit 0
    else
        printf "\r⏳ Waiting... (%ds) - /health -> %s" "$elapsed" "$response"
    fi

    sleep 5
done
